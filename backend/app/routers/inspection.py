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
  * (v146) a supervisor reply while an attached file is still UNREAD → 422,
    naming the file and the characters left. The owner asked for uploads up to
    100 MB and added the requirement that decides the design: «حجم هم باعث نشه
    ناظر نتونه بگه من نمیخونمش». The text is extracted at upload, served in
    slices, and the slices are counted — so reading is cheap and skipping it is
    visible. The owner's own notes are never blocked by this; only the reviewer's.
"""
from __future__ import annotations

import contextvars
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     Response, UploadFile)
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.inspection import (
    BINDER_CAPACITY,
    EXTRACT_LABEL,
    OUTCOME_FIXED,
    OUTCOME_NEEDS_OWNER,
    OUTCOMES,
    STATUS_ANSWERED,
    STATUS_APPROVED,
    STATUS_FILED,
    STATUS_OPEN,
    URGENT_CLAIM_TTL_S,
    InspectionBinder,
    InspectionFile,
    InspectionReport,
    InspectionShot,
    file_read_debt,
    sheet_glow,
)
from app.models.system_setting import SystemSetting
from app.services.supervisor_rounds import next_round, record_round
from app.routers.auth import get_current_active_user
from app.services import inspection_files as ifiles
from app.services.audit import record_audit

router = APIRouter(tags=["inspection"], dependencies=[Depends(get_current_active_user)])

MAX_TEXT = 6000
#: v175 — HOW BIG A PICTURE MAY BE, and why there is a number here at all.
#
# «این خطایی که موقع ثبت گزارش میزنم و ریشه‌ای درست کن که محدودیتی نباشه».
#
# The owner pasted their own screenshot and the report was REFUSED: «String
# should have at most 1400000 characters». The old ceiling was about a megabyte
# of base64 — smaller than an ordinary full-screen PNG — so the one thing that
# makes this system worth having, a real picture of what they saw, was the thing
# it turned away.
#
# The real fix is on the page: the browser now re-encodes every picture, pasted
# or rendered, down to something sane before it is ever sent (see
# `frontend/src/lib/shrinkShot.ts`). A screenshot is evidence for a human and a
# text model; it never needs to be ten megabytes. So in practice there is no
# limit any more — nothing the owner can paste reaches this number.
#
# The number itself stays, generously, because the picture travels inside a JSON
# body and is decoded in memory: without ANY ceiling a single request could take
# the server down, which would be a worse failure than a refused screenshot. It
# is now ~12 MB of base64 (~9 MB of image), far above anything the page sends.
MAX_SHOT_BYTES = 12_000_000
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


def _check_shot_size(v: Optional[str]) -> Optional[str]:
    """The schema-level guard, in a sentence the owner can act on.

    v175 — this used to be `Field(max_length=1_400_000)`, so a pasted screenshot
    came back as «shot: String should have at most 1400000 characters» — English,
    about a field name nobody has heard of, and with no hint of what to do. The
    ceiling is now ~12 MB and the page shrinks pictures before sending, so this
    should be unreachable; if it ever fires it says so in words.
    """
    if isinstance(v, str) and len(v) > MAX_SHOT_BYTES:
        raise ValueError(
            f"تصویر بیش از حد بزرگ است (~{len(v) // 1_000_000} مگابایت). "
            "صفحه تصویرها را پیش از ارسال کوچک می‌کند؛ اگر این پیام را می‌بینی "
            "یعنی آن مرحله اجرا نشده — صفحه را تازه کن و دوباره تلاش کن.")
    return v


def _split_data_url(shot: Optional[str]) -> Optional[tuple]:
    """`(mime, base64)` for a well-formed image data URL, else None.

    v175 — OVERSIZE IS NO LONGER SILENT. This used to return None for a picture
    that was too big, exactly as it does for «this is not an image», so a shot
    that squeezed past the request schema was DROPPED without a word: the sheet
    filed with no picture and nobody was told. The two cases are not the same —
    one is «there was nothing to store», the other is «you sent something and we
    threw it away» — so the size case raises now, and says what to do.
    """
    if not isinstance(shot, str) or not shot.startswith(_DATA_URL):
        return None
    if len(shot) > MAX_SHOT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"تصویر بیش از حد بزرگ است ({len(shot) // 1_000_000} مگابایت). "
                   "صفحه تصویرها را پیش از ارسال کوچک می‌کند؛ اگر این پیام را "
                   "می‌بینی یعنی آن مرحله اجرا نشده — صفحه را تازه کن و دوباره بچسبان.")
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


def _file_dict(f: InspectionFile) -> dict:
    """One attached file as the UI and the supervisor both need to see it.

    `read` is included on purpose: the supervisor can see its own debt before it
    tries to answer, instead of discovering it as a 422.
    """
    total = int(f.text_chars or 0)
    got = int(f.read_chars or 0)
    return {
        "id": f.id,
        "report_id": f.report_id,
        "note_id": f.note_id or "",
        "filename": f.filename or "",
        "mime": f.mime or "",
        "byte_size": int(f.byte_size or 0),
        "size_label": ifiles.human_size(f.byte_size or 0),
        "caption": f.caption or "",
        "uploaded_by": f.uploaded_by or "",
        "created_at": f.created_at.isoformat() if f.created_at else None,
        # where the bytes really are — «local» means they die with the next deploy
        "store": f.store or "",
        "store_note": f.store_note or "",
        "drive_link": f.drive_link or "",
        "durable": (f.store or "") == "drive",
        # what there is to read, and what it cost to not be readable
        "extract_status": f.extract_status or "pending",
        "extract_label": EXTRACT_LABEL.get(f.extract_status or "pending", ""),
        "extract_note": f.extract_note or "",
        "text_chars": total,
        "page_count": int(f.page_count or 0),
        # true ⇒ the text is NOT the whole file; the file itself must be opened
        "text_truncated": bool(f.text_truncated),
        # the proof, in the open
        "read_chars": got,
        "read_percent": (round(100 * got / total) if total else None),
        "fully_read": bool(total and got >= total),
        "read_at": f.read_at.isoformat() if f.read_at else None,
        "read_by": f.read_by or "",
        "viewed_at": f.viewed_at.isoformat() if f.viewed_at else None,
    }


async def _files_of(db: AsyncSession, report_id: str) -> List[InspectionFile]:
    return list((await db.execute(
        select(InspectionFile).where(InspectionFile.report_id == report_id)
        .order_by(InspectionFile.created_at))).scalars().all())


async def _files_by_report(db: AsyncSession, report_ids: List[str]) -> dict:
    """Files for MANY sheets in one query.

    The queue is the supervisor's first screen of every round, so it has to show
    which sheets carry samples — but one query per sheet would make the list cost
    grow with the wall. The `text` column is excluded: a listing must never ship
    megabytes of extracted text (the same reason shots live in their own table).
    """
    out: dict = {rid: [] for rid in report_ids}
    if not report_ids:
        return out
    cols = (InspectionFile.id, InspectionFile.report_id, InspectionFile.note_id,
            InspectionFile.filename, InspectionFile.mime, InspectionFile.byte_size,
            InspectionFile.caption, InspectionFile.uploaded_by, InspectionFile.created_at,
            InspectionFile.store, InspectionFile.store_note, InspectionFile.drive_link,
            InspectionFile.extract_status, InspectionFile.extract_note,
            InspectionFile.text_chars, InspectionFile.page_count,
            # v146 — MUST be selected: `file_read_debt` reads it, and a column
            # missing from a listing reads as False, so the queue would report
            # «nothing to read» on a file the answer endpoint then refuses.
            InspectionFile.text_truncated,
            InspectionFile.read_chars, InspectionFile.read_at, InspectionFile.read_by,
            InspectionFile.viewed_at)
    rows = (await db.execute(
        select(*cols).where(InspectionFile.report_id.in_(report_ids))
        .order_by(InspectionFile.created_at))).all()
    for row in rows:
        # a light stand-in with the same attribute names `_file_dict` reads
        out.setdefault(row.report_id, []).append(_FileRow(row))
    return out


class _FileRow:
    """Attribute view over a partial row, so `_file_dict`/`file_read_debt` work
    on a listing exactly as they do on a full ORM object."""

    __slots__ = ("_m",)

    def __init__(self, row) -> None:
        self._m = row._mapping

    def __getattr__(self, name: str):
        try:
            return self._m[name]
        except KeyError:
            # `text` is deliberately not loaded in listings
            return "" if name == "text" else None


def _to_dict(r: InspectionReport, deps: bool = True, files: Optional[list] = None) -> dict:
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
        # v150 — where the box really was. `None` for sheets filed before this
        # existed; the overlay simply does not draw those, rather than guessing.
        "geometry": json.loads(r.geometry_json) if (r.geometry_json or "").strip() else None,
        "notes": notes,
        "dependencies": _deps(r) if deps else [],
        "glow": sheet_glow(r.status, notes),
        # v155 — where this sheet stands in the fast queue
        **_urgent_state(r),
        # v146 — the attached samples, and what the supervisor still owes on them
        "files": [_file_dict(f) for f in (files or [])],
        "read_debt": file_read_debt(files or []),
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
    fmap = await _files_by_report(db, [r.id for r in rows])
    return {"ok": True,
            "reports": [_to_dict(r, files=fmap.get(r.id, [])) for r in rows],
            "counts": counts, "binder_capacity": BINDER_CAPACITY}


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
    fmap = await _files_by_report(db, [r.id for r in rows])
    reports = [_to_dict(r, files=fmap.get(r.id, [])) for r in rows]
    # v167 — «نیمه‌کاره» IS STILL WORK, AND IT HAS TO COME BACK.
    #
    # Until now `owed` counted only the untouched sheets, so the moment the
    # supervisor wrote `partial` the sheet dropped out of what it owed and
    # nothing ever brought the remainder back: the label said «بخشی انجام شد؛
    # بقیه‌اش…» and the «بقیه» was owed to nobody. `not-done` was worse — its own
    # hint says «این برگه هنوز کارِ نکرده دارد» while the round reported a clean
    # exit. The owner asked the obvious question: «یادش می‌مونه؟»
    #
    # The rule is now the one the colour already implies: a sheet is finished
    # only when the work is DONE WITH PROOF (`fixed` + its after picture) or
    # parked on the owner's decision (`needs-owner`). Everything else — partial,
    # not-done, a reply with no outcome at all — is still owed and comes back
    # next round. `unfinished` is reported separately from `unanswered` so the
    # round can say «۲ تازه، ۱ نیمه‌کاره» rather than one undifferentiated number.
    unanswered = [r for r in reports if r["status"] == STATUS_OPEN]
    unfinished = [r for r in reports if r["status"] == STATUS_ANSWERED
                  and (r.get("glow") or {}).get("tone") not in (OUTCOME_FIXED, OUTCOME_NEEDS_OWNER)]
    return {
        "ok": True,
        "owed": len(unanswered) + len(unfinished),
        "unanswered": len(unanswered),
        "unfinished": len(unfinished),
        "unfinished_numbers": [r["number"] for r in unfinished],
        "waiting_for_owner": len(rows) - len(unanswered) - len(unfinished),
        "to_file": (await db.execute(
            select(func.count(InspectionReport.id))
            .where(InspectionReport.status == STATUS_APPROVED))).scalar() or 0,
        # v146 — the reading the supervisor owes, up front on its first screen,
        # so an unread sample is visible before it drafts an answer.
        "files_to_read": sum(len(r["read_debt"]) for r in reports),
        "reports": reports,
    }


# ---------------------------------------------------------------------------
# v146 — FILES. Any type, up to 100 MB, and the reviewer has to read them.
#
# The upload is multipart and streamed: a 100 MB body must never be assembled in
# a JSON string (the screenshot path is a data-URL and is capped at ~1.4 MB for
# exactly that reason). Text is extracted ONCE, here, so the reviewer reads text
# instead of bytes; the reading endpoint counts what it served.
# ---------------------------------------------------------------------------
#: Read in pieces so a 100 MB upload never sits in memory twice.
_UPLOAD_CHUNK = 1024 * 1024


@router.post("/{report_id}/files")
async def upload_file(
    report_id: str,
    file: UploadFile = File(...),
    caption: str = Form(""),
    note_id: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """Attach one file of ANY type to a sheet.

    The owner's use cases, verbatim: a non-image sample for a page that does not
    exist yet; an image downloaded from elsewhere (not a screenshot); a Word or
    PDF sample of a document format to be built from. All three are «here is a
    specimen, read it», so the caption travels with the bytes and the text is
    pulled out for the reviewer.
    """
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")

    # Read with a running total so an oversized body is refused mid-stream
    # instead of after the whole thing has been buffered.
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = await file.read(_UPLOAD_CHUNK)
        if not chunk:
            break
        size += len(chunk)
        if size > ifiles.MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(f"حجمِ فایل از سقفِ {ifiles.MAX_MB} مگابایت بیشتر است. "
                        "اگر لازم است بالاتر برود، INSPECTION_MAX_FILE_MB را زیاد کن"))
        chunks.append(chunk)
    data = b"".join(chunks)
    chunks.clear()
    if not data:
        raise HTTPException(status_code=422, detail="فایل خالی است")

    filename = ifiles.safe_filename(file.filename or "file")
    mime = (file.content_type or "").strip() or "application/octet-stream"

    # Extract BEFORE storing: if the bytes cannot be kept, the reviewer at least
    # still gets the readable content instead of nothing.
    ex = ifiles.extract(data, filename, mime)
    try:
        placed = await ifiles.store(data=data, filename=filename, mime=mime,
                                    report_number=int(r.number or 0))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502,
                            detail=f"ذخیرهٔ فایل ممکن نشد: {exc}"[:300]) from exc

    fid = uuid.uuid4().hex[:24]
    row = InspectionFile(
        id=fid, report_id=r.id, note_id=_clean(note_id, 40),
        uploaded_by=str(getattr(user, "username", "") or ""),
        filename=placed["filename"], mime=mime, byte_size=placed["byte_size"],
        sha256=placed["sha256"], caption=_clean(caption, MAX_TEXT),
        store=placed["store"], drive_id=placed["drive_id"],
        drive_link=placed["drive_link"], local_path=placed["local_path"],
        store_note=placed["store_note"],
        extract_status=ex["status"], extract_note=ex["note"],
        text=ex["text"], text_chars=len(ex["text"] or ""),
        page_count=int(ex.get("page_count") or 0),
        text_truncated=bool(ex.get("truncated")),
    )
    db.add(row)
    # An upload is a change to the sheet, so it re-opens an answered one: the
    # owner has handed over new material and the previous answer did not see it.
    if r.status == STATUS_ANSWERED and not await _is_supervisor(db, user):
        r.status = STATUS_OPEN
    await db.commit()
    await db.refresh(row)
    # `r` may have been modified above (a new sample re-opens an answered sheet),
    # which expires it on commit — refresh before it is serialised, or building
    # the response triggers lazy IO outside the async context.
    await db.refresh(r)
    await record_audit(
        action="inspection_file_upload", entity_type="inspection", entity_id=r.id,
        detail=(f"گزارشِ {r.number} — «{row.filename}» "
                f"({ifiles.human_size(row.byte_size)}، {row.store or 'نامشخص'}، "
                f"استخراج: {row.extract_status})"),
        user=user, db=db)
    return {"ok": True, "file": _file_dict(row),
            "report": _to_dict(r, files=await _files_of(db, r.id))}


async def _file_or_404(db: AsyncSession, file_id: str) -> InspectionFile:
    row = (await db.execute(select(InspectionFile).where(
        InspectionFile.id == file_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="فایل پیدا نشد")
    return row


@router.get("/files/{file_id}")
async def file_meta(file_id: str, db: AsyncSession = Depends(get_db),
                    user=Depends(get_current_active_user)):
    return {"ok": True, "file": _file_dict(await _file_or_404(db, file_id))}


@router.get("/files/{file_id}/text")
async def file_text(
    file_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """Serve the extracted text in slices, and RECORD how far the reader got.

    This is the mechanism behind «size must not be an excuse»: the reviewer never
    needs the bytes, and cannot pretend to have read what it did not fetch.
    `read_chars` only ever moves forward, and only to what was actually served —
    a reader that jumps to the end has still not read the middle.
    """
    row = await _file_or_404(db, file_id)
    text = row.text or ""
    total = len(text)
    # a caller may ask for a bigger bite — bounded, so one request can never be
    # asked to serialise an arbitrary amount
    n = min(limit or ifiles.SLICE_CHARS, ifiles.MAX_SLICE_CHARS)
    part = text[offset:offset + n]
    end = offset + len(part)

    # Only a CONTIGUOUS read counts. Skipping ahead leaves the gap unread, which
    # is the honest answer — otherwise one call to the last page would clear the
    # whole debt.
    if offset <= int(row.read_chars or 0) and end > int(row.read_chars or 0):
        row.read_chars = end
        row.read_at = datetime.now(timezone.utc)
        row.read_by = str(getattr(user, "username", "") or "")
        await db.commit()
        await db.refresh(row)

    return {
        "ok": True,
        "file_id": row.id,
        "filename": row.filename or "",
        "caption": row.caption or "",
        "extract_status": row.extract_status or "",
        "extract_note": row.extract_note or "",
        "offset": offset,
        "returned": len(part),
        "text": part,
        # the same coverage discipline as v144: never report a slice as the whole
        "text_chars": total,
        "has_more": end < total,
        "next_offset": end if end < total else None,
        "read_chars": int(row.read_chars or 0),
        "fully_read": int(row.read_chars or 0) >= total and total > 0,
        "page_count": int(row.page_count or 0),
    }


@router.get("/files/{file_id}/raw")
async def file_raw(file_id: str, db: AsyncSession = Depends(get_db),
                   user=Depends(get_current_active_user)):
    """The bytes themselves — for images, and for anything with no extractor.

    Fetching this is what «looked at it» means for a file that has no text, so it
    is recorded: `file_read_debt` demands it rather than waving images through.
    """
    row = await _file_or_404(db, file_id)
    try:
        data = await ifiles.load(row)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=410, detail=str(exc)[:300]) from exc
    row.viewed_at = datetime.now(timezone.utc)
    await db.commit()
    # inline for an image so the browser shows it; everything else downloads
    disp = "inline" if (row.mime or "").startswith("image/") else "attachment"
    # v152 — a Persian filename cannot go in a latin-1 header. Building this by
    # hand returned 500 for every one of the owner's samples; the shared helper
    # does RFC 5987 and neutralises quote/CRLF injection from the uploaded name.
    from app.utils.http_headers import content_disposition

    return Response(
        content=data, media_type=row.mime or "application/octet-stream",
        headers={"Content-Disposition": content_disposition(disp, row.filename or "file"),
                 "Cache-Control": "private, max-age=300"})


@router.post("/files/{file_id}/extract")
async def extract_file(file_id: str, db: AsyncSession = Depends(get_db),
                       user=Depends(get_current_active_user)):
    """(Re)read one attachment with today's readers — and for audio/video (or an
    archive holding some) produce the FULL transcript (services/inspection_media).

    The supervisor's `pull` calls it for every file still `pending`. New text is
    a new reading duty, so the read counter starts over.
    """
    import asyncio

    from app.services import inspection_media as imedia

    row = await _file_or_404(db, file_id)
    try:
        data = await ifiles.load(row)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=410, detail=str(exc)[:300]) from exc
    if not data:
        raise HTTPException(status_code=410, detail="بایت‌های این فایل در دسترس نیست")
    token = _GEMINI_KEY.set(await _gemini_key(db))
    try:
        name, mime = row.filename or "", row.mime or ""
        ex = await asyncio.to_thread(
            lambda: imedia.finish_extraction(ifiles.extract(data, name, mime), data, name, mime))
    finally:
        _GEMINI_KEY.reset(token)
    text = ex["text"] or ""
    if text != (row.text or ""):
        row.read_chars, row.read_at = 0, None
    row.extract_status, row.extract_note, row.text = ex["status"], ex["note"], text
    row.text_chars, row.text_truncated = len(text), bool(ex.get("truncated"))
    row.page_count = int(ex.get("page_count") or 0)
    await db.commit()
    await db.refresh(row)
    await record_audit(
        action="inspection_file_extract", entity_type="inspection", entity_id=row.report_id,
        detail=f"«{row.filename}» — استخراج: {row.extract_status}، {row.text_chars} نویسه",
        user=user, db=db)
    return {"ok": True, "success": True, "file": _file_dict(row)}


#: The Gemini key from «AI settings» (DB), handed to the transcription thread —
#: asyncio.to_thread copies the context, so the sync KEY_PROVIDERS hook sees it.
_GEMINI_KEY: "contextvars.ContextVar[Optional[str]]" = contextvars.ContextVar("inspection_gemini_key", default=None)


async def _gemini_key(db: AsyncSession) -> Optional[str]:
    try:
        from app.ai.manager import AIManager
        from app.models.ai_config import AIProvider

        p = (await db.execute(select(AIProvider).where(AIProvider.key == "gemini"))).scalar_one_or_none()
        return AIManager.effective_api_key(p) if p is not None else None
    except Exception:  # noqa: BLE001 — env vars remain the fallback
        return None


def _register_key_provider() -> None:
    from app.services import inspection_media as imedia

    if _GEMINI_KEY.get not in imedia.KEY_PROVIDERS:
        imedia.KEY_PROVIDERS.insert(0, _GEMINI_KEY.get)


_register_key_provider()


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, db: AsyncSession = Depends(get_db),
                      user=Depends(get_current_active_user)):
    """Only the OWNER removes a sample. The supervisor cannot delete its homework.

    Same shape as the sheet-delete guard: a rule that is only written down is a
    rule that gets broken. The Drive copy is deliberately LEFT in place — the
    binding rule is quarantine, not deletion, and a sample the owner sent is
    evidence.
    """
    if await _is_supervisor(db, user):
        raise HTTPException(status_code=403,
                            detail="ناظر فایلِ نمونه را حذف نمی‌کند — این کارِ مالک است")
    row = await _file_or_404(db, file_id)
    rid, name = row.report_id, row.filename
    await db.delete(row)
    await db.commit()
    await record_audit(action="inspection_file_delete", entity_type="inspection",
                       entity_id=rid, detail=f"«{name}» از برگه برداشته شد (نسخهٔ درایو دست‌نخورده ماند)",
                       user=user, db=db)
    return {"ok": True}


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


# NOTE — this must stay ABOVE `/{report_id}`. A literal path declared after a
# path parameter is never reached: FastAPI matched «/urgent» as a report id and
# answered with a 404-shaped report lookup instead of the queue. Caught by the
# tests, not by reading.
@router.get("/urgent")
async def urgent_queue(db: AsyncSession = Depends(get_db),
                       user=Depends(get_current_active_user)):
    """The fast queue, oldest request first — the order the owner pressed them."""
    rows = (await db.execute(
        select(InspectionReport)
        .where(InspectionReport.urgent_at.isnot(None),
               InspectionReport.urgent_done_at.is_(None),
               InspectionReport.status != STATUS_FILED)
        .order_by(InspectionReport.urgent_at)
    )).scalars().all()
    fmap = await _files_by_report(db, [r.id for r in rows])
    out = []
    for i, r in enumerate(rows):
        d = _to_dict(r, files=fmap.get(r.id, []))
        d["position"] = i + 1
        d["claimable"] = _claim_expired(r)
        out.append(d)
    return {"ok": True, "waiting": len(out), "reports": out,
            "next_round": await _next_round(db)}


@router.get("/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db),
                     user=Depends(get_current_active_user)):
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    return {"ok": True, "report": _to_dict(r, files=await _files_of(db, r.id))}


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
    #: v150 — the precise measurement (document coords, scroll, dpr, and the
    #: anchor element's verified selector with the box as fractions of it).
    #: Optional: an older client still files a perfectly good sheet without it.
    geometry: Optional[dict] = None


class CreateIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT)
    spot: SpotIn
    shot: Optional[str] = None

    _shot_size = field_validator("shot")(_check_shot_size)


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
        geometry_json=json.dumps(s.geometry, ensure_ascii=False) if s.geometry else "",
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
    return {"ok": True, "report": _to_dict(r, files=await _files_of(db, r.id))}


class NoteIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT)
    shot: Optional[str] = None

    _shot_size = field_validator("shot")(_check_shot_size)
    #: Supervisor only — what really happened.
    outcome: Optional[str] = Field(None, max_length=16)
    #: Supervisor only — proof it looked after fixing.
    after_shot: Optional[str] = None

    _after_size = field_validator("after_shot")(_check_shot_size)
    commits: List[str] = Field(default_factory=list, max_length=20)
    #: Supervisor only — the dependency walk behind the answer.
    dependencies: List[dict] = Field(default_factory=list, max_length=60)
    #: v158 — a follow-up written from inside «نظارت» carries its OWN box: the
    #: owner draws a new rectangle on a new place and files it UNDER an existing
    #: sheet. Notes are stored as JSON, so this needs no migration, and the parent
    #: sheet's own spot is never overwritten.
    spot: Optional[SpotIn] = None
    #: v158 — files uploaded FOR THIS NOTE. They are attached first (the note has
    #: no id until it exists), then claimed here, so a follow-up's samples do not
    #: land in the same undifferentiated pile as the original report's. The owner:
    #: «فایل هایی که پیوستش میخوام بکنم نباید قاتی فایل های پیوست قبلی باشه».
    file_ids: List[str] = Field(default_factory=list, max_length=40)


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

    # v146 — THE RULE THAT MAKES «I WON'T READ IT» IMPOSSIBLE.
    #
    # The owner attached samples so the supervisor would read them: «هم به
    # محتوای کامل فایل باید توجه بشه هم به توضیحات و اسکرین», and «حجم هم باعث
    # نشه ناظر نتونه بگه من نمیخونمش». Reading is already cheap — the text was
    # extracted at upload and is served in slices — so an unread sample is a
    # choice, and this refuses it. The owner's own notes are never blocked.
    if reviewer:
        debt = file_read_debt(await _files_of(db, r.id))
        if debt:
            parts = []
            for d in debt[:6]:
                if d["reason"] == "text":
                    parts.append(f"«{d['filename']}»: {d['remaining']} نویسه از "
                                 f"{d['text_chars']} خوانده نشده")
                elif d["reason"] == "truncated":
                    parts.append(f"«{d['filename']}»: متنش بریده شده بود، پس باید "
                                 "خودِ فایل را هم باز کنی")
                else:
                    parts.append(f"«{d['filename']}»: هنوز باز نشده")
            raise HTTPException(
                status_code=422,
                detail=("پیش از پاسخ باید فایل‌های پیوستِ برگه را کامل بخوانی — "
                        + "؛ ".join(parts)
                        + ". متن را از /api/inspection/files/{id}/text تکه‌تکه بگیر "
                          "(و برای تصویر/فایلِ بی‌متن، /raw را باز کن)"),
            )

    nid = uuid.uuid4().hex[:16]
    shot_id = await _store_shot(db, r.id, nid, "before", payload.shot)
    after_id = await _store_shot(db, r.id, nid, "after", payload.after_shot) if reviewer else None

    note = {
        "id": nid, "by": "reviewer" if reviewer else "owner", "at": _now(),
        "text": text, "author": str(getattr(user, "username", "") or ""),
        "shot_id": shot_id,
    }
    if payload.spot is not None:
        sp = payload.spot
        note["spot"] = {
            "page": _clean(sp.page, 200), "page_label": _clean(sp.page_label, 200),
            "section_id": _clean(sp.section_id, 120),
            "section_label": _clean(sp.section_label, 200),
            "reopen": _clean(sp.reopen, 240), "dom_path": _clean(sp.dom_path, 400),
            "covered_text": _clean(sp.covered_text, MAX_TEXT),
            "rect": sp.rect if isinstance(sp.rect, dict) else None,
            "viewport": sp.viewport if isinstance(sp.viewport, dict) else None,
            "geometry": sp.geometry if isinstance(sp.geometry, dict) else None,
        }
    if reviewer:
        note["outcome"] = payload.outcome
        note["after_shot_id"] = after_id
        note["commits"] = [_clean(c, 60) for c in (payload.commits or [])][:20]

    notes = _notes(r)
    notes.append(note)
    r.notes_json = json.dumps(notes, ensure_ascii=False)

    # Claim the files this note was written with. Only UNCLAIMED files of THIS
    # sheet can be claimed: a file already belonging to an earlier note can never
    # be pulled out from under it by a later one.
    if payload.file_ids:
        wanted = [_clean(x, 40) for x in payload.file_ids if _clean(x, 40)][:40]
        if wanted:
            rows = (await db.execute(select(InspectionFile).where(
                InspectionFile.id.in_(wanted),
                InspectionFile.report_id == r.id,
            ))).scalars().all()
            for fr in rows:
                if not (fr.note_id or ""):
                    fr.note_id = nid

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
        # v155 — the urgent request is DISCHARGED by the answer, which is what
        # was asked for. `urgent_at` is kept (not cleared) so the page can say
        # «the thing you rushed has been answered» instead of the row silently
        # dropping out of the queue as though it had never been asked.
        if r.urgent_at is not None and r.urgent_done_at is None:
            r.urgent_done_at = datetime.now(timezone.utc)
            r.urgent_claimed_at = None
            r.urgent_claimed_by = ""
    else:
        # v158 — these two were an `elif` chain, and that was a bug the owner hit:
        # a sheet that had been rushed AND answered took the first branch and
        # NEVER reached the status reset, so the owner wrote a follow-up and the
        # sheet stayed «answered» — still green, still saying «درست شد», while
        # they were asking for more. Two independent facts need two independent
        # statements.
        if r.urgent_done_at is not None:
            # they are asking again, so it goes back into the fast queue at its
            # ORIGINAL position — nobody loses their place for adding a note
            r.urgent_done_at = None
        if r.status in (STATUS_ANSWERED, STATUS_APPROVED):
            # The owner writing again means it is not settled. APPROVED is
            # included deliberately: the tick was theirs, and so is taking it
            # back. FILED is not — an archived sheet is closed for good.
            r.status = STATUS_OPEN
    await db.commit()
    await db.refresh(r)
    await record_audit(
        action="inspection_reviewer_note" if reviewer else "inspection_owner_note",
        entity_type="inspection", entity_id=r.id,
        detail=f"گزارشِ {r.number} — " + (f"نتیجه: {payload.outcome}" if reviewer else "یادداشتِ مالک"),
        user=user, db=db)
    return {"ok": True, "report": _to_dict(r, files=await _files_of(db, r.id))}


# ---------------------------------------------------------------------------
# v155 — «فوری»: jump the queue, without two runs colliding.
# ---------------------------------------------------------------------------
def _urgent_state(r: InspectionReport) -> dict:
    """Everything the UI needs to say where this sheet stands, and nothing more."""
    claimed = r.urgent_claimed_at is not None and not _claim_expired(r)
    return {
        "urgent": r.urgent_at is not None and r.urgent_done_at is None,
        "urgent_at": r.urgent_at.isoformat() if r.urgent_at else None,
        "urgent_done_at": r.urgent_done_at.isoformat() if r.urgent_done_at else None,
        # «in hand right now» — so the owner sees movement instead of silence
        "urgent_in_progress": claimed and r.urgent_done_at is None,
        "urgent_claimed_by": (r.urgent_claimed_by or "") if claimed else "",
        # v156 — WHEN it was taken and when the claim lapses. Without these, a
        # sheet that is merely «not claimable» looks identical to one stuck
        # forever, and the only way to tell them apart is to wait and see.
        "urgent_claimed_at": _utc(r.urgent_claimed_at) if claimed else None,
        "urgent_claim_expires_at": (
            _utc(r.urgent_claimed_at, plus=URGENT_CLAIM_TTL_S) if claimed else None),
    }


def _utc(dt, plus: int = 0):
    """An ISO timestamp that always carries a zone.

    SQLite hands back naive datetimes while PostgreSQL hands back aware ones, so
    emitting `dt.isoformat()` directly makes the SAME field zoned on one
    deployment and zone-less on another — and a client that subtracts two of them
    gets a TypeError rather than a wrong answer, which is at least loud. Both
    timestamps in this payload go through here so they are always comparable.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt + timedelta(seconds=plus)).isoformat()


def _claim_expired(r: InspectionReport) -> bool:
    """A claim outlives its run only up to the TTL — otherwise one crash parks a
    sheet until somebody notices, which is the failure this queue exists to end."""
    if r.urgent_claimed_at is None:
        return True
    started = r.urgent_claimed_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - started).total_seconds() > URGENT_CLAIM_TTL_S


@router.post("/{report_id}/urgent")
async def mark_urgent(report_id: str, db: AsyncSession = Depends(get_db),
                      user=Depends(get_current_active_user)):
    """The owner asks for this one NOW, ahead of the twice-weekly round.

    Pressing it again does NOT move the sheet to the back or the front: the
    original request time stands, because «whichever I pressed first» is the
    promise, and re-pressing must not quietly reorder the queue.
    """
    if await _is_supervisor(db, user):
        raise HTTPException(status_code=403, detail="درخواستِ فوری کارِ مالک است، نه ناظر")
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    if r.status == STATUS_FILED:
        raise HTTPException(status_code=422, detail="برگهٔ بایگانی‌شده نوبتِ فوری نمی‌گیرد")
    if r.urgent_at is None or r.urgent_done_at is not None:
        r.urgent_at = datetime.now(timezone.utc)
        r.urgent_done_at = None
        r.urgent_claimed_at = None
        r.urgent_claimed_by = ""
        await db.commit()
        await db.refresh(r)
        await record_audit(action="inspection_urgent", entity_type="inspection",
                           entity_id=r.id, detail=f"برگهٔ {r.number} فوری شد",
                           user=user, db=db)
    ahead = await _urgent_ahead(db, r)
    # v168 — the owner presses ⚡ and immediately wants to know WHEN. The instant
    # is returned in UTC and rendered in the reader's own local time by the page:
    # the server never guesses a timezone, because «۱۹ دقیقهٔ دیگر» has to be
    # right on the clock the owner is actually looking at.
    return {"ok": True, "position": ahead + 1, "next_round": await _next_round(db),
            "report": _to_dict(r, files=await _files_of(db, r.id))}


@router.delete("/{report_id}/urgent")
async def unmark_urgent(report_id: str, db: AsyncSession = Depends(get_db),
                        user=Depends(get_current_active_user)):
    """Take it out of the fast queue. The sheet itself is untouched."""
    if await _is_supervisor(db, user):
        raise HTTPException(status_code=403, detail="لغوِ فوری کارِ مالک است")
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    r.urgent_at = None
    r.urgent_claimed_at = None
    r.urgent_claimed_by = ""
    r.urgent_done_at = None
    await db.commit()
    await db.refresh(r)
    return {"ok": True, "report": _to_dict(r, files=await _files_of(db, r.id))}


# ---------------------------------------------------------------------------
# v168 — «چند دقیقهٔ دیگر می‌رود سراغش؟»
#
# The fast round is a Routine in claude.ai; this server cannot read its
# schedule, so it MEASURES it instead. The round knocks here every time it runs
# (it claims the queue even when the queue is empty), and those knocks are the
# only honest source for a countdown. The arithmetic lives in
# `services/supervisor_rounds.py`, tested without a scheduler; this is just the
# row it is kept in — `system_settings`, which is already in the backup, so no
# new table and no new surface to extend (rule 6).
# ---------------------------------------------------------------------------
ROUND_LOG_KEY = "inspection_urgent_rounds"


async def _round_log(db: AsyncSession) -> str | None:
    row = (await db.execute(select(SystemSetting)
                            .where(SystemSetting.key == ROUND_LOG_KEY))).scalar_one_or_none()
    return row.value if row else None


async def _note_round(db: AsyncSession) -> None:
    """The supervisor just knocked. Kept on its own, never inside another
    commit's failure path: a lost heartbeat must not cost a claimed sheet."""
    row = (await db.execute(select(SystemSetting)
                            .where(SystemSetting.key == ROUND_LOG_KEY))).scalar_one_or_none()
    value = record_round(row.value if row else None, datetime.now(timezone.utc))
    if row:
        row.value = value
    else:
        db.add(SystemSetting(key=ROUND_LOG_KEY, value=value))
    await db.commit()


async def _next_round(db: AsyncSession) -> dict:
    return next_round(datetime.now(timezone.utc), await _round_log(db))


async def _urgent_ahead(db: AsyncSession, r: InspectionReport) -> int:
    """How many still-waiting sheets were asked for BEFORE this one."""
    if r.urgent_at is None:
        return 0
    return int((await db.execute(
        select(func.count(InspectionReport.id)).where(
            InspectionReport.urgent_at.isnot(None),
            InspectionReport.urgent_done_at.is_(None),
            InspectionReport.status != STATUS_FILED,
            InspectionReport.urgent_at < r.urgent_at,
        ))).scalar() or 0)


class ClaimIn(BaseModel):
    by: str = Field("", max_length=80)


@router.post("/urgent/claim")
async def claim_next_urgent(payload: ClaimIn, db: AsyncSession = Depends(get_db),
                            user=Depends(get_current_active_user)):
    """Take the NEXT urgent sheet, one at a time.

    The whole point is that two runs never work the same sheet: a second run
    would write a second answer to a sheet the first is already changing, which
    is the «تناقض» this has to avoid. So the claim is written and committed
    BEFORE the caller is told which sheet it got, and a sheet already claimed
    within the TTL is skipped rather than handed out again.

    Returns `{report: null}` when there is nothing to do — which is the normal
    case on most runs, and must be cheap and quiet, not an error.
    """
    if not await _is_supervisor(db, user):
        raise HTTPException(status_code=403, detail="صفِ فوری را فقط ناظر برمی‌دارد")
    # v168 — THE HEARTBEAT. This call is made on EVERY run, including the very
    # common one that finds the queue empty, which is exactly what makes it a
    # usable clock: it is the round announcing itself. Recorded before any of
    # the work below, so a run that then fails still counts as «it came».
    await _note_round(db)
    rows = (await db.execute(
        select(InspectionReport)
        .where(InspectionReport.urgent_at.isnot(None),
               InspectionReport.urgent_done_at.is_(None),
               InspectionReport.status != STATUS_FILED)
        .order_by(InspectionReport.urgent_at)
    )).scalars().all()
    nxt = next((r for r in rows if _claim_expired(r)), None)
    if nxt is None:
        return {"ok": True, "report": None,
                "waiting": len(rows), "busy": len(rows)}
    nxt.urgent_claimed_at = datetime.now(timezone.utc)
    nxt.urgent_claimed_by = _clean(payload.by, 80) or str(getattr(user, "username", "") or "")
    await db.commit()
    await db.refresh(nxt)
    return {"ok": True, "waiting": len(rows),
            "report": _to_dict(nxt, files=await _files_of(db, nxt.id))}


class EditNoteIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT)


@router.patch("/{report_id}/notes/{note_id}")
async def edit_note(report_id: str, note_id: str, payload: EditNoteIn,
                    db: AsyncSession = Depends(get_db),
                    user=Depends(get_current_active_user)):
    """v152 — correct what a note SAYS, in place.

    The owner asked to edit the report itself rather than append: «باید بشه خود
    گزارش ادیت زد … الان به شکلی که گویا گزارشی در ادامهٔ گزارشِ قبل داری ثبت
    می‌کنی». Adding a correction as a new note leaves the wrong text at the top of
    the sheet, which is the text the supervisor reads first.

    WHAT IS KEPT, BECAUSE A SHEET IS A RECORD
      * the ORIGINAL text is preserved on the note as `original_text` the first
        time it is edited, and `edited_at` marks it. Nothing is overwritten
        without trace — this is the same instinct as rule 2: quarantine, not
        delete. The board shows «ویرایش شد» and can show what it said before.
      * you may only edit YOUR OWN kind of note. The owner cannot rewrite the
        supervisor's answer and the supervisor cannot rewrite the owner's
        report — otherwise the conversation stops being evidence of anything.
      * a FILED sheet is closed. It lives in a binder; editing history there
        would make the archive worthless.
    """
    r = (await db.execute(select(InspectionReport).where(
        InspectionReport.id == report_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    if r.status == STATUS_FILED:
        raise HTTPException(status_code=422,
                            detail="برگهٔ بایگانی‌شده ویرایش نمی‌شود — تاریخچه باید دست‌نخورده بماند")
    text = _clean(payload.text)
    if not text:
        raise HTTPException(status_code=422, detail="متنِ یادداشت خالی است")

    reviewer = await _is_supervisor(db, user)
    notes = _notes(r)
    target = next((n for n in notes if n.get("id") == note_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="یادداشت پیدا نشد")
    mine = "reviewer" if reviewer else "owner"
    if (target.get("by") or "owner") != mine:
        raise HTTPException(
            status_code=403,
            detail=("یادداشتِ طرفِ مقابل ویرایش نمی‌شود — "
                    "اگر نظری داری، یادداشتِ تازه بنویس"))

    if not target.get("original_text"):
        target["original_text"] = target.get("text", "")
    target["text"] = text
    target["edited_at"] = _now()
    # the sheet's headline is the first line of the FIRST note
    if notes and notes[0].get("id") == note_id:
        r.title = _headline(text)
    r.notes_json = json.dumps(notes, ensure_ascii=False)
    await db.commit()
    await db.refresh(r)
    await record_audit(action="inspection_note_edit", entity_type="inspection",
                       entity_id=r.id, detail=f"یادداشتِ برگهٔ {r.number} ویرایش شد",
                       user=user, db=db)
    return {"ok": True, "report": _to_dict(r, files=await _files_of(db, r.id))}


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
    return {"ok": True, "report": _to_dict(r, files=await _files_of(db, r.id))}


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
    # v149 — the attached samples go with the sheet. Until this run they did NOT:
    # `InspectionFile` arrived in v146 and this handler was never updated, so
    # deleting a sheet left its file rows behind pointing at a report that no
    # longer existed. Every listing filters by `report_id`, so those rows were
    # unreachable from anywhere in the product while still holding up to 20M
    # characters of extracted text each.
    #
    # This is the orphaned-import-attachment finding again (run 2, OPEN_ITEMS #5):
    # «the file is not lost — but it cannot be found either», which for whoever is
    # looking for it is the same thing. The neighbour gave it away: shots were
    # cleaned up two lines above, and a difference with no reason is a finding.
    #
    # The DRIVE copy is deliberately left in place, exactly as `delete_file` does:
    # rule 2 is quarantine, not deletion, and a sample the owner sent is evidence.
    removed = 0
    for f in (await db.execute(select(InspectionFile).where(
            InspectionFile.report_id == report_id))).scalars().all():
        await db.delete(f)
        removed += 1
    await db.delete(r)
    await db.commit()
    await record_audit(
        action="inspection_delete", entity_type="inspection", entity_id=report_id,
        detail=(f"برگهٔ {r.number} حذف شد"
                + (f" — {removed} فایلِ پیوست هم از پرونده برداشته شد "
                   "(نسخهٔ درایو دست‌نخورده ماند)" if removed else "")),
        user=user, db=db)
    return {"ok": True, "files_removed": removed}
