"""Interactive CRM actions on the merged credit-file data (wired at /api/crm).

Phase 3 — makes the customer profile actionable (not just a read-only view of the
merged Excel data). Wave B: toggle the 9-step credit-file checklist, recording
each change to the activity journal (mirrors the Excel MarkChecklistRowComplete /
SubmitChecklist + WriteToJournal).
"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.crm import ChecklistProgress, CHECKLIST_STEPS, JournalEntry
from app.routers.auth import require_editor

router = APIRouter(tags=["crm"])

_DONE = {"✓", "1", "true", "yes", "done"}


def _is_done(v) -> bool:
    return str(v or "").strip().lower() in _DONE or v == "✓"


class StepToggle(BaseModel):
    step: int = Field(..., ge=1, le=9)
    done: bool


@router.patch("/checklist/{account_no}")
async def toggle_checklist_step(
    account_no: str,
    payload: StepToggle,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Mark a credit-file workflow step done/pending and log it to the journal."""
    cp = (
        await db.execute(select(ChecklistProgress).where(ChecklistProgress.account_no == account_no))
    ).scalar_one_or_none()
    if cp is None:
        cp = ChecklistProgress(account_no=account_no)
        db.add(cp)

    setattr(cp, f"item{payload.step}", "✓" if payload.done else "")
    cp.total = str(sum(1 for i in range(1, 10) if _is_done(getattr(cp, f"item{i}", ""))))
    cp.last_action = date.today().isoformat()
    cp.last_user = getattr(user, "username", "") or ""

    step_name = CHECKLIST_STEPS[payload.step - 1]
    db.add(JournalEntry(
        id="J-" + uuid.uuid4().hex[:18],
        account_no=account_no,
        account_name=cp.account_name or "",
        item=step_name,
        status="✓" if payload.done else "",
        action="Submit" if payload.done else "Unmark",
        source="Panel Checklist",
        date=date.today().isoformat(),
        user=getattr(user, "username", "") or "",
    ))
    await db.commit()
    return {"account_no": account_no, "step": payload.step, "done": payload.done, "total": cp.total}
