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
from app.models.guarantor import Guarantor
from app.models.customer import Customer
from app.models.facility import Facility, FacilityType
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


# ---------------------------------------------------------------------------
# Guarantors (add a guarantor + security cheque to a customer)
# ---------------------------------------------------------------------------
class GuarantorCreate(BaseModel):
    guarantor_name: str = Field(..., min_length=1, max_length=200)
    guarantor_account: str = ""
    cheque_no: str = ""
    cheque_amount: Optional[float] = None
    issuing_bank: str = "BSI"
    pim_ref: str = ""


@router.post("/guarantors/{account_no}")
async def add_guarantor(
    account_no: str,
    payload: GuarantorCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Add a guarantor + security cheque to a customer."""
    gid = f"G-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:2]}"
    g = Guarantor(
        id=gid, account_no=account_no, guarantor_name=payload.guarantor_name[:200],
        guarantor_account=(payload.guarantor_account or "")[:50], cheque_no=(payload.cheque_no or "")[:50],
        cheque_amount=payload.cheque_amount, issuing_bank=(payload.issuing_bank or "BSI")[:50],
        pim_ref=(payload.pim_ref or "")[:80], date_added=date.today().isoformat(),
        created_by=getattr(user, "username", "") or "",
    )
    db.add(g)
    await db.commit()
    return {
        "id": g.id, "account_no": g.account_no, "guarantor_name": g.guarantor_name,
        "guarantor_account": g.guarantor_account, "cheque_no": g.cheque_no,
        "cheque_amount": float(g.cheque_amount) if g.cheque_amount is not None else None,
        "issuing_bank": g.issuing_bank, "pim_ref": g.pim_ref,
    }


# ---------------------------------------------------------------------------
# Facilities (add a facility to a customer, linked via account_no)
# ---------------------------------------------------------------------------
def _facility_type(raw: str) -> FacilityType:
    u = (raw or "").strip().lower()
    if "overdraft" in u or u == "od":
        return FacilityType.OVERDRAFT
    if "loan" in u:
        return FacilityType.LOAN
    if u == "lc" or "letter of credit" in u:
        return FacilityType.LC
    if u == "lg" or "guarantee" in u:
        return FacilityType.LG
    return FacilityType.OTHER


class FacilityCreate(BaseModel):
    facility_type: str = "loan"
    amount: float = Field(..., ge=0)
    currency: str = "AED"
    name: str = ""  # facility / offer-letter reference


@router.post("/facilities/{account_no}")
async def add_facility(
    account_no: str,
    payload: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Add a facility to a customer (resolved by account_no)."""
    cid = (
        await db.execute(select(Customer.id).where(Customer.account_no == account_no))
    ).scalar_one_or_none()
    if not cid:
        raise HTTPException(status_code=404, detail="Customer not found for this account")
    fid = f"F-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    f = Facility(
        id=fid, customer_id=cid, name=(payload.name or "")[:200], amount=payload.amount,
        currency=(payload.currency or "AED")[:3], facility_type=_facility_type(payload.facility_type),
        risk_rating="medium", is_deleted=False,
    )
    db.add(f)
    await db.commit()
    return {
        "id": f.id, "name": f.name, "amount": float(f.amount or 0),
        "currency": f.currency, "facility_type": f.facility_type.value,
        "status": "active", "outstanding": 0,
    }
