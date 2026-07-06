"""Saved official letters — wired at /api/letters.

Save a letter UNDER a customer account (auto-creating the customer's profile if it
doesn't exist yet, exactly like collateral/facilities do) or as a GENERAL letter.
Each letter keeps its own values + layout, so per-letter edits never touch the
master template.
"""
import json
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.models.letter import Letter, generate_letter_id
from app.routers.auth import require_editor, get_current_active_user
from app.services.audit import record_audit
from app.services.customer_link import ensure_customer

router = APIRouter(tags=["letters"], dependencies=[Depends(get_current_active_user)])


def _dumps(v: Any) -> Optional[str]:
    return json.dumps(v, ensure_ascii=False) if v is not None else None


def _loads(s: Optional[str]) -> Any:
    try:
        return json.loads(s) if s else None
    except Exception:
        return None


class LetterSummary(BaseModel):
    id: str
    account_no: Optional[str] = None
    category: str
    title: Optional[str] = None
    subject: Optional[str] = None
    recipient_dept: Optional[str] = None
    recipient_manager: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class LetterFull(LetterSummary):
    values: Any = None
    layout: Any = None
    labels: Any = None


class LetterSave(BaseModel):
    account_no: Optional[str] = Field(default=None, max_length=50)
    general: bool = False
    title: Optional[str] = Field(default=None, max_length=255)
    subject: Optional[str] = Field(default=None, max_length=500)
    recipient_dept: Optional[str] = Field(default=None, max_length=200)
    recipient_manager: Optional[str] = Field(default=None, max_length=200)
    values: Any = None
    layout: Any = None
    labels: Any = None


def _summary(l: Letter) -> LetterSummary:
    return LetterSummary.model_validate(l)


@router.get("/", response_model=List[LetterSummary])
async def list_letters(
    db: AsyncSession = Depends(get_db),
    account_no: Optional[str] = Query(None),
    general: bool = Query(False),
):
    base = select(Letter).where(Letter.is_deleted == False)  # noqa: E712
    if general:
        base = base.where(Letter.category == "general")
    elif account_no:
        base = base.where(Letter.account_no == account_no)
    rows = (await db.execute(base.order_by(Letter.updated_at.desc().nullslast(), Letter.created_at.desc()).limit(500))).scalars().all()
    return [_summary(r) for r in rows]


@router.get("/{letter_id}", response_model=LetterFull)
async def get_letter(letter_id: str, db: AsyncSession = Depends(get_db)):
    l = (await db.execute(select(Letter).where(Letter.id == letter_id, Letter.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if l is None:
        raise HTTPException(status_code=404, detail="Letter not found")
    out = LetterFull.model_validate(l)
    out.values, out.layout, out.labels = _loads(l.values_json), _loads(l.layout_json), _loads(l.labels_json)
    return out


async def _apply(l: Letter, p: LetterSave, db, user):
    acc = (p.account_no or "").strip()
    if acc and not p.general:
        await ensure_customer(db, acc, None)  # auto-create the customer's profile if new
        l.account_no = acc
        l.category = "account"
    else:
        l.account_no = None
        l.category = "general"
    l.title = (p.title or "").strip()[:255] or None
    l.subject = (p.subject or "").strip()[:500] or None
    l.recipient_dept = (p.recipient_dept or "").strip()[:200] or None
    l.recipient_manager = (p.recipient_manager or "").strip()[:200] or None
    if p.values is not None:
        l.values_json = _dumps(p.values)
    if p.layout is not None:
        l.layout_json = _dumps(p.layout)
    if p.labels is not None:
        l.labels_json = _dumps(p.labels)
    l.updated_by = getattr(user, "username", "") or ""


@router.post("/", response_model=LetterFull, status_code=201)
async def create_letter(payload: LetterSave, request: Request, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    l = Letter(id=generate_letter_id(), created_by=getattr(user, "username", "") or "")
    await _apply(l, payload, db, user)
    db.add(l)
    await db.commit()
    await db.refresh(l)
    await record_audit(action="create", entity_type="letter", entity_id=l.id, account_no=l.account_no,
                       detail=f"ذخیرهٔ نامه{(' — ' + l.title) if l.title else ''}{'' if l.account_no else ' (عمومی)'}",
                       user=user, request=request, db=db)
    out = LetterFull.model_validate(l)
    out.values, out.layout, out.labels = _loads(l.values_json), _loads(l.layout_json), _loads(l.labels_json)
    return out


@router.patch("/{letter_id}", response_model=LetterFull)
async def update_letter(letter_id: str, payload: LetterSave, request: Request, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    l = (await db.execute(select(Letter).where(Letter.id == letter_id, Letter.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if l is None:
        raise HTTPException(status_code=404, detail="Letter not found")
    await _apply(l, payload, db, user)
    await db.commit()
    await db.refresh(l)
    await record_audit(action="update", entity_type="letter", entity_id=l.id, account_no=l.account_no,
                       detail=f"ویرایشِ نامه{(' — ' + l.title) if l.title else ''}", user=user, request=request, db=db)
    out = LetterFull.model_validate(l)
    out.values, out.layout, out.labels = _loads(l.values_json), _loads(l.layout_json), _loads(l.labels_json)
    return out


@router.get("/{letter_id}/attachments")
async def list_letter_attachments(letter_id: str, db: AsyncSession = Depends(get_db)):
    """The letter's uploaded enclosures (پیوست‌ها). Uploads go through the shared
    /api/crm/attachments endpoint with facility_id=LTR-<letter id> — so the files
    live in Drive (attachments/cust-<acc>/fac-LTR-<id>, traceable names) with a
    disk fallback, AND automatically appear under the customer profile's
    attachments (they're keyed by the same account_no)."""
    from app.models.crm import Attachment

    rows = (
        await db.execute(
            select(Attachment).where(Attachment.facility_id == f"LTR-{letter_id}")
            .order_by(Attachment.upload_date.desc())
        )
    ).scalars().all()
    return [{
        "id": a.id, "account_no": a.account_no, "original_name": a.original_name,
        "file_size": a.file_size, "upload_date": a.upload_date, "uploaded_by": a.uploaded_by,
        "storage": "drive" if (a.drive_file_id or "") else "disk",
    } for a in rows]


@router.delete("/{letter_id}", status_code=204)
async def delete_letter(letter_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    l = (await db.execute(select(Letter).where(Letter.id == letter_id, Letter.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if l is None:
        raise HTTPException(status_code=404, detail="Letter not found")
    l.is_deleted = True
    await db.commit()
    await record_audit(action="delete", entity_type="letter", entity_id=l.id, account_no=l.account_no,
                       detail=f"حذفِ نامه{(' — ' + l.title) if l.title else ''}", user=user, request=request, db=db)
    return None
