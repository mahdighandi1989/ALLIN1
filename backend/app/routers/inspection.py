"""v141 — «نظارت و سرکشی»: the owner's inspection sheets over the system's screens.

THE LOOP
    owner draws a box on any screen  →  a sheet is filed with the way BACK to it
    →  the weekly supervisor reads the queue, does the work, writes the result
       UNDER the sheet with its dependency walk and (for a claimed fix) an
       after-picture  →  the owner looks and ticks  →  the next round archives it.

WHAT THIS ROUTER REFUSES, AND WHY (each one paid for in the sibling project):

  * `outcome='fixed'` with no after-shot → 422. A supervisor that cannot show
    the result writes `not-done`; a false green makes the owner stop looking.
  * the supervisor's own account calling `approve` → 403. The tick is the
    owner's, and a rule that is only written down is a rule that gets broken.
  * a note with no text → 422. «پاسخ دادم» must mean something was said.
  * a remote URL as a shot → dropped. Only a data-URL is accepted, so this can
    never be turned into a server-side request forgery.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.inspection import (
    BINDER_CAPACITY,
    OUTCOME_FIXED,
    OUTCOMES,
    STATUS_ANSWERED,
    STATUS_APPROVED,
    STATUS_FILED,
    STATUS_OPEN,
    InspectionBinder,
    InspectionReport,
    InspectionShot,
    sheet_glow,
)
from app.routers.auth import get_current_active_user
from app.services.audit import record_audit

router = APIRouter(tags=["inspection"], dependencies=[Depends(get_current_active_user)])

MAX_TEXT = 6000
MAX_SHOT_BYTES = 1_400_000
#: Only the sheets still on the wall count. Archived ones live forever.
MAX_ACTIVE = int(os.getenv("INSPECTION_MAX_ACTIVE", "500"))

_DATA_URL = "data:image/"
_ALLOWED_MIME = ("image/png", "image/jpeg", "image/webp")


async def _supervisor_username(db: AsyncSession) -> str:
    """The account the weekly supervisor signs in as.

    Its notes are `reviewer` notes (and only it may record an outcome), and it
    is REFUSED the owner's tick. The name is read from the editable setting
    first, so the owner can change it from the Settings page without a redeploy,
    and falls back to the environment for a fresh deployment.

    IMPORTANT — this must be configured on the SERVER, not only in whatever
    environment the supervisor itself runs in. If the server does not know the
    name, nobody is the supervisor: no outcome can be recorded (fail-closed,
    which is right) but the tick would also be open to it (fail-OPEN, which is
    not). So `set_status` refuses outright while this is unset, rather than
    silently trusting the caller.
    """
    from app.models.system_setting import SystemSetting

    row = (await db.execute(select(SystemSetting).where(
        SystemSetting.key == "supervisor_username"))).scalar_one_or_none()
    name = str(getattr(row, "value", "") or "").strip()
    if not name:
        name = (os.getenv("SUPERVISOR_API_USER") or "").strip()
    return name.lower()


async def _is_supervisor(db: AsyncSession, user) -> bool:
    name = str(getattr(user, "username", "") or "").strip().lower()
    sup = await _supervisor_username(db)
    return bool(sup) and name == sup


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(v: Any, limit: int = MAX_TEXT) -> str:
    return str(v or "").replace("\x00", "")[:limit].strip()


def _split_data_url(shot: Optional[str]) -> Optional[tuple]:
    """`(mime, base64)` for a well-formed image data URL, else None."""
    if not isinstance(shot, str) or not shot.startswith(_DATA_URL):
        return None
    if len(shot) > MAX_SHOT_BYTES:
        return None
    try:
        head, payload = shot.split(",", 1)
    except ValueError:
        return None
    mime = head[5:].split(";")[0]
    if mime not in _ALLOWED_MIME or not payload:
        return None
    return mime, payload


def _notes(report: InspectionReport) -> List[dict]:
    try:
        v = json.loads(report.notes_json or "[]")
        return v if isinstance(v, list) else []
    except Exception:  # noqa: BLE001 - a corrupt row must not break the page
        return []


def _deps(report: InspectionReport) -> List[dict]:
    try:
        v = json.loads(report.deps_json or "[]")
        return v if isinstance(v, list) else []
    except Exception:  # noqa: BLE001
        return []


def _headline(text: str) -> str:
    first = next((ln for ln in text.split("\n") if ln.strip()), "بدونِ عنوان")
    return first.strip()[:120]


async def _store_shot(db: AsyncSession, report_id: str, note_id: str, kind: str,
                      shot: Optional[str]) -> Optional[str]:
    parsed = _split_data_url(shot)
    if parsed is None:
        return None
    mime, payload = parsed
    sid = uuid.uuid4().hex[:24]
    db.add(InspectionShot(id=sid, report_id=report_id, note_id=note_id, kind=kind,
                          mime=mime, data=payload, byte_size=len(payload)))
    return sid


def _to_dict(r: InspectionReport, deps: bool = True) -> dict:
    notes = _notes(r)
    return {
        "id": r.id,
        "number": r.number,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "status": r.status,
        "title": r.title or "",
        "created_by": r.created_by or "",
        "page": r.page or "",
        "page_label": r.page_label or "",
        "section_id": r.section_id or "",
        "section_label": r.section_label or "",
        "reopen": r.reopen or "",
        "dom_path": r.dom_path or "",
        "covered_text": r.covered_text or "",
        "rect": json.loads(r.rect_json or "null") if r.rect_json else None,
        "viewport": json.loads(r.viewport_json or "null") if r.viewport_json else None,
        "notes": notes,
        "dependencies": _deps(r) if deps else [],
        "glow": sheet_glow(r.status, notes),
        "binder": ({"id": r.binder_id, "number": r.binder_number, "page": r.binder_page}
                   if r.binder_id else None),
    }


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
@router.get("")
@router.get("/")
async def list_reports(
    status: Optional[str] = Query(None),
    reopen: Optional[str] = Query(None, description="فقط برگه‌های همین بخش"),
    include_filed: bool = Query(False),
    limit: int = Query(300, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    q = select(InspectionReport)
    if status:
        q = q.where(InspectionReport.status == status)
    elif not include_filed:
        q = q.where(InspectionReport.status != STATUS_FILED)
    if reopen:
        q = q.where(InspectionReport.reopen == reopen)
    rows = (await db.execute(q.order_by(InspectionReport.number.desc()).limit(limit))).scalars().all()
    counts = {s: 0 for s in (STATUS_OPEN, STATUS_ANSWERED, STATUS_APPROVED, STATUS_FILED)}
    for s, n in (await db.execute(
        select(InspectionReport.status, func.count(InspectionReport.id))
        .group_by(InspectionReport.status)
    )).all():
        counts[s] = int(n or 0)
    return {"ok": True, "reports": [_to_dict(r) for r in rows], "counts": counts,
            "binder_capacity": BINDER_CAPACITY}


@router.get("/queue")
async def queue(db: AsyncSession = Depends(get_db), user=Depends(get_current_active_user)):
    """What the supervisor OWES an answer on — the first job of every round.

    A sheet the supervisor already replied to is still here until the owner
    ticks it, because «answered» is not «finished»: the owner may write back.
    """
    rows = (await db.execute(
        select(InspectionReport)
        .where(InspectionReport.status.in_([STATUS_OPEN, STATUS_ANSWERED]))
        .order_by(InspectionReport.number)
    )).scalars().all()
    unanswered = [r for r in rows if r.status == STATUS_OPEN]
    return {
        "ok": True,
        "owed": len(unanswered),
        "waiting_for_owner": len(rows) - len(unanswered),
        "to_file": (await db.execute(
            select(func.count(InspectionReport.id))
            .where(InspectionReport.status == STATUS_APPROVED))).scalar() or 0,
        "reports": [_to_dict(r) for r in rows],
    }


@router.get("/shots/{shot_id}")
async def get_shot(shot_id: str, db: AsyncSession = Depends(get_db),
                   user=Depends(get_current_active_user)):
    import base64

    shot = (await db.execute(select(InspectionShot).where(
        InspectionShot.id == shot_id))).scalar_one_or_none()
    if shot is None:
        raise HTTPException(status_code=404, detail="تصویر پیدا نشد")
    try:
        raw = base64.b64decode(shot.data or "")
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=422, detail="تصویر خوانده نشد")
    return Response(content=raw, media_type=shot.mime or "image/jpeg",
                    headers={"Cache-Control": "private, max-age=86400"})


@router.get("/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db),
                     user=Depends(get_current_active_user)):
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    return {"ok": True, "report": _to_dict(r)}


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
class SpotIn(BaseModel):
    page: str = Field("", max_length=200)
    page_label: str = Field("", max_length=200)
    section_id: str = Field("", max_length=120)
    section_label: str = Field("", max_length=200)
    reopen: str = Field("", max_length=240)
    dom_path: str = Field("", max_length=400)
    covered_text: str = Field("", max_length=MAX_TEXT)
    rect: Optional[dict] = None
    viewport: Optional[dict] = None


class CreateIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT)
    spot: SpotIn
    shot: Optional[str] = Field(None, max_length=MAX_SHOT_BYTES)


@router.post("")
@router.post("/")
async def create_report(payload: CreateIn, db: AsyncSession = Depends(get_db),
                        user=Depends(get_current_active_user)):
    text = _clean(payload.text)
    if not text:
        raise HTTPException(status_code=422, detail="متنِ گزارش خالی است")
    active = (await db.execute(select(func.count(InspectionReport.id)).where(
        InspectionReport.status != STATUS_FILED))).scalar() or 0
    if active >= MAX_ACTIVE:
        raise HTTPException(status_code=422,
                            detail=f"سقفِ {MAX_ACTIVE} برگهٔ باز پر است — اول چند تا را تأیید و بایگانی کن")
    top = (await db.execute(select(func.max(InspectionReport.number)))).scalar() or 0
    rid = uuid.uuid4().hex[:24]
    nid = uuid.uuid4().hex[:16]
    s = payload.spot
    shot_id = await _store_shot(db, rid, nid, "before", payload.shot)
    note = {"id": nid, "by": "owner", "at": _now(), "text": text,
            "author": str(getattr(user, "username", "") or ""),
            "shot_id": shot_id}
    r = InspectionReport(
        id=rid, number=int(top) + 1, status=STATUS_OPEN, title=_headline(text),
        created_by=str(getattr(user, "username", "") or ""),
        page=_clean(s.page, 200), page_label=_clean(s.page_label, 200),
        section_id=_clean(s.section_id, 120), section_label=_clean(s.section_label, 200),
        reopen=_clean(s.reopen, 240), dom_path=_clean(s.dom_path, 400),
        covered_text=_clean(s.covered_text),
        rect_json=json.dumps(s.rect or {}, ensure_ascii=False),
        viewport_json=json.dumps(s.viewport or {}, ensure_ascii=False),
        notes_json=json.dumps([note], ensure_ascii=False),
        deps_json="[]",
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    # v141 — the loop is visible on the Audit Log page too, so «what happened to
    # my reports» is answerable from the place the owner already looks.
    await record_audit(action="inspection_report_created", entity_type="inspection",
                       entity_id=r.id, detail=f"گزارشِ {r.number} — {r.title} ({r.reopen})",
                       user=user, db=db)
    return {"ok": True, "report": _to_dict(r)}


class NoteIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT)
    shot: Optional[str] = Field(None, max_length=MAX_SHOT_BYTES)
    #: Supervisor only — what really happened.
    outcome: Optional[str] = Field(None, max_length=16)
    #: Supervisor only — proof it looked after fixing.
    after_shot: Optional[str] = Field(None, max_length=MAX_SHOT_BYTES)
    commits: List[str] = Field(default_factory=list, max_length=20)
    #: Supervisor only — the dependency walk behind the answer.
    dependencies: List[dict] = Field(default_factory=list, max_length=60)


@router.post("/{report_id}/notes")
async def add_note(report_id: str, payload: NoteIn, db: AsyncSession = Depends(get_db),
                   user=Depends(get_current_active_user)):
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    text = _clean(payload.text)
    if not text:
        raise HTTPException(status_code=422, detail="متنِ یادداشت خالی است")

    reviewer = await _is_supervisor(db, user)
    if payload.outcome is not None:
        if not reviewer:
            raise HTTPException(status_code=422, detail="«نتیجه» را فقط ناظر ثبت می‌کند")
        if payload.outcome not in OUTCOMES:
            raise HTTPException(status_code=422, detail="نتیجهٔ نامعتبر")
        # THE RULE THAT MAKES THE COLOUR HONEST: a claimed fix needs its picture.
        if payload.outcome == OUTCOME_FIXED and not _split_data_url(payload.after_shot):
            raise HTTPException(
                status_code=422,
                detail="«درست شد» بدونِ تصویرِ بعدش پذیرفته نمی‌شود — یا تصویر بفرست یا نتیجه را «نیمه‌کاره»/«درست نشد» بگذار",
            )

    nid = uuid.uuid4().hex[:16]
    shot_id = await _store_shot(db, r.id, nid, "before", payload.shot)
    after_id = await _store_shot(db, r.id, nid, "after", payload.after_shot) if reviewer else None

    note = {
        "id": nid, "by": "reviewer" if reviewer else "owner", "at": _now(),
        "text": text, "author": str(getattr(user, "username", "") or ""),
        "shot_id": shot_id,
    }
    if reviewer:
        note["outcome"] = payload.outcome
        note["after_shot_id"] = after_id
        note["commits"] = [_clean(c, 60) for c in (payload.commits or [])][:20]

    notes = _notes(r)
    notes.append(note)
    r.notes_json = json.dumps(notes, ensure_ascii=False)

    if reviewer and payload.dependencies:
        deps = _deps(r)
        for d in payload.dependencies[:60]:
            if isinstance(d, dict):
                deps.append({"name": _clean(d.get("name"), 160),
                             "status": _clean(d.get("status"), 20),
                             "note": _clean(d.get("note"), 300)})
        r.deps_json = json.dumps(deps, ensure_ascii=False)

    # A supervisor answer moves the conversation on; an owner follow-up on an
    # answered sheet re-opens it, because the owner is asking again.
    if reviewer:
        if r.status in (STATUS_OPEN, STATUS_ANSWERED):
            r.status = STATUS_ANSWERED
    elif r.status == STATUS_ANSWERED:
        r.status = STATUS_OPEN
    await db.commit()
    await db.refresh(r)
    await record_audit(
        action="inspection_reviewer_note" if reviewer else "inspection_owner_note",
        entity_type="inspection", entity_id=r.id,
        detail=f"گزارشِ {r.number} — " + (f"نتیجه: {payload.outcome}" if reviewer else "یادداشتِ مالک"),
        user=user, db=db)
    return {"ok": True, "report": _to_dict(r)}


class StatusIn(BaseModel):
    status: str = Field(..., max_length=12)


@router.post("/{report_id}/status")
async def set_status(report_id: str, payload: StatusIn, db: AsyncSession = Depends(get_db),
                     user=Depends(get_current_active_user)):
    """The owner's tick (and un-tick). The supervisor is refused here.

    In the sibling project this was a written rule. A rule that is only written
    down is a rule that gets broken by the next well-meaning change, so here the
    boundary is a guard.
    """
    want = (payload.status or "").strip()
    if want not in (STATUS_OPEN, STATUS_APPROVED):
        raise HTTPException(status_code=422, detail="فقط «open» یا «approved» پذیرفته می‌شود")
    if await _is_supervisor(db, user):
        raise HTTPException(status_code=403,
                            detail="تیکِ تأیید فقط دستِ مالک است — ناظر نمی‌تواند کارِ خودش را تأیید کند")
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    r.status = want
    await db.commit()
    await db.refresh(r)
    await record_audit(action="inspection_approved" if want == STATUS_APPROVED else "inspection_reopened",
                       entity_type="inspection", entity_id=r.id,
                       detail=f"گزارشِ {r.number} — {r.title}", user=user, db=db)
    return {"ok": True, "report": _to_dict(r)}


@router.post("/file")
async def file_approved(db: AsyncSession = Depends(get_db),
                        user=Depends(get_current_active_user)):
    """Move every ticked sheet into a binder. Run by the supervisor each round."""
    rows = (await db.execute(select(InspectionReport)
                             .where(InspectionReport.status == STATUS_APPROVED)
                             .order_by(InspectionReport.number))).scalars().all()
    if not rows:
        return {"ok": True, "filed": 0, "binders": []}

    binders = (await db.execute(select(InspectionBinder)
                                .order_by(InspectionBinder.number))).scalars().all()
    current = next((b for b in reversed(binders) if b.closed_at is None), None)
    touched: list = []
    for r in rows:
        ids = json.loads(current.report_ids_json or "[]") if current else []
        if current is None or len(ids) >= BINDER_CAPACITY:
            if current is not None:
                current.closed_at = datetime.now(timezone.utc)
            n = (max((b.number for b in binders), default=0) + 1) if binders else 1
            current = InspectionBinder(
                id=uuid.uuid4().hex[:24], number=n,
                label=f"زونکنِ نظارت — شمارهٔ {n}",
                subtitle="برگه‌های تأییدشدهٔ نظارت و سرکشی",
                report_ids_json="[]")
            db.add(current)
            binders = list(binders) + [current]
            ids = []
        ids.append(r.id)
        current.report_ids_json = json.dumps(ids, ensure_ascii=False)
        r.status = STATUS_FILED
        r.binder_id = current.id
        r.binder_number = current.number
        r.binder_page = len(ids)
        touched.append({"number": r.number, "binder": current.number, "page": len(ids)})
    await db.commit()
    await record_audit(action="inspection_filed", entity_type="inspection",
                       detail=f"{len(touched)} برگه بایگانی شد", user=user, db=db)
    return {"ok": True, "filed": len(touched), "pages": touched}


@router.delete("/{report_id}")
async def delete_report(report_id: str, db: AsyncSession = Depends(get_db),
                        user=Depends(get_current_active_user)):
    if await _is_supervisor(db, user):
        raise HTTPException(status_code=403, detail="ناظر نمی‌تواند برگه حذف کند")
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    for s in (await db.execute(select(InspectionShot).where(
            InspectionShot.report_id == report_id))).scalars().all():
        await db.delete(s)
    await db.delete(r)
    await db.commit()
    return {"ok": True}
