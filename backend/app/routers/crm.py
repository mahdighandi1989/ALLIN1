"""Interactive CRM actions on the merged credit-file data (wired at /api/crm).

Phase 3 — makes the customer profile actionable (not just a read-only view of the
merged Excel data). Wave B: toggle the 9-step credit-file checklist, recording
each change to the activity journal (mirrors the Excel MarkChecklistRowComplete /
SubmitChecklist + WriteToJournal).
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
from app.models.crm import ChecklistProgress, CHECKLIST_STEPS, JournalEntry, CustomTask
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


# ---------------------------------------------------------------------------
# Tasks / follow-ups (add + complete/deactivate)
# ---------------------------------------------------------------------------
def _task_dict(t: CustomTask) -> dict:
    return {
        "id": t.id, "account_no": t.account_no, "facility_id": t.facility_id,
        "task_name": t.task_name, "status": t.status, "followup_date": t.followup_date,
        "notes": t.notes, "priority": t.priority, "created_by": t.created_by,
        "created_date": t.created_date, "completed_date": t.completed_date, "is_active": t.is_active,
    }


class TaskCreate(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=200)
    followup_date: str = ""
    priority: str = "Medium"
    notes: str = ""
    facility_id: str = ""


@router.post("/tasks/{account_no}")
async def create_task(
    account_no: str,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Add a follow-up task for a customer."""
    tid = f"T-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    t = CustomTask(
        id=tid, account_no=account_no, facility_id=(payload.facility_id or "")[:60],
        task_name=payload.task_name[:200], status="", followup_date=(payload.followup_date or "")[:30],
        notes=payload.notes or "", priority=(payload.priority or "Medium")[:20],
        created_by=getattr(user, "username", "") or "", created_date=date.today().isoformat(),
        completed_date="", is_active="1",
    )
    db.add(t)
    await db.commit()
    return _task_dict(t)


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    is_active: Optional[str] = None


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Complete (status) or deactivate (is_active='0') a task."""
    t = (await db.execute(select(CustomTask).where(CustomTask.id == task_id))).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.status is not None:
        t.status = payload.status[:30]
        if payload.status.strip().lower() in ("done", "completed", "✓"):
            t.completed_date = date.today().isoformat()
    if payload.is_active is not None:
        t.is_active = payload.is_active[:5]
    await db.commit()
    return _task_dict(t)
