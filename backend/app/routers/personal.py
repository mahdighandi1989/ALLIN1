"""Private per-user personal notes + one-button email digest (A8/A11/A16).

Mounted at /api/personal. Every note is scoped to the signed-in user, so one
user never sees another's notes. ``POST /notes/send-email`` emails the user's
UNSENT notes (formatted, with the configured key + signature) and marks them
sent — the web/SMTP equivalent of the Excel SendUnsentNotesToEmail (a true
Outlook integration / scheduled auto-send needs Microsoft Graph + a worker and
is out of scope here).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.personal import PersonalNote
from app.models.system_setting import SystemSetting
from app.utils.security import get_current_user

router = APIRouter(tags=["personal"], dependencies=[Depends(get_current_user)])


def _uname(user) -> str:
    return getattr(user, "username", None) or getattr(user, "email", None) or "user"


def _dict(n: PersonalNote) -> dict:
    return {
        "id": n.id, "content": n.content, "category": n.category,
        "is_done": bool(n.is_done), "is_sent": bool(n.is_sent),
        "created_date": n.created_date,
    }


async def _setting(db, key: str, default: str = "") -> str:
    row = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    return (getattr(row, "value", None) or default) if row else default


@router.get("/notes")
async def list_notes(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    rows = (
        await db.execute(
            select(PersonalNote).where(PersonalNote.username == _uname(user)).order_by(PersonalNote.created_at.desc())
        )
    ).scalars().all()
    return {"items": [_dict(n) for n in rows], "total": len(rows)}


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1)
    category: str = "General"


@router.post("/notes")
async def add_note(payload: NoteCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    n = PersonalNote(
        id=f"PN-{uuid.uuid4().hex[:18]}", username=_uname(user), content=payload.content,
        category=(payload.category or "General")[:60], is_done=False, is_sent=False,
        created_date=date.today().isoformat(),
    )
    db.add(n)
    await db.commit()
    return _dict(n)


class NoteUpdate(BaseModel):
    is_done: Optional[bool] = None
    content: Optional[str] = None


async def _owned(db, note_id: str, user) -> PersonalNote:
    n = (
        await db.execute(
            select(PersonalNote).where(PersonalNote.id == note_id, PersonalNote.username == _uname(user))
        )
    ).scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return n


@router.patch("/notes/{note_id}")
async def update_note(note_id: str, payload: NoteUpdate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    n = await _owned(db, note_id, user)
    if payload.is_done is not None:
        n.is_done = payload.is_done
    if payload.content is not None:
        n.content = payload.content
    await db.commit()
    return _dict(n)


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    n = await _owned(db, note_id, user)
    await db.delete(n)
    await db.commit()
    return {"ok": True, "id": note_id, "deleted": True}


@router.post("/notes/send-email")
async def send_notes_email(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Email this user's UNSENT notes, then mark them sent (A16)."""
    from app.services.email import send_email, smtp_configured

    if not smtp_configured():
        raise HTTPException(status_code=400, detail="SMTP is not configured (set SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD).")
    uname = _uname(user)
    to = (await _setting(db, "personal_notes_email")) or getattr(user, "email", "") or ""
    if not to:
        raise HTTPException(status_code=400, detail="No target email — set 'Personal notes — email to' in Settings.")
    unsent = (
        await db.execute(
            select(PersonalNote).where(PersonalNote.username == uname, PersonalNote.is_sent == False)  # noqa: E712
            .order_by(PersonalNote.created_at)
        )
    ).scalars().all()
    if not unsent:
        return {"ok": True, "sent": 0, "message": "No unsent notes"}

    key = await _setting(db, "personal_notes_key")
    sig = await _setting(db, "personal_notes_signature")
    lines = [f"Personal notes — {uname}", f"Generated {datetime.utcnow():%Y-%m-%d %H:%M} UTC", ""]
    for n in unsent:
        lines.append(f"[{'x' if n.is_done else ' '}] ({n.category or 'General'}) {n.content}")
    if key:
        lines += ["", f"Key: {key}"]
    if sig:
        lines += ["", sig]
    ok, msg = await send_email(to, f"Personal notes ({len(unsent)})", "\n".join(lines))
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    for n in unsent:
        n.is_sent = True
    await db.commit()
    return {"ok": True, "sent": len(unsent), "to": to}
