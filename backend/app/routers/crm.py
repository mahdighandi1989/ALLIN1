"""Interactive CRM actions on the merged credit-file data (wired at /api/crm).

Phase 3 — makes the customer profile actionable (not just a read-only view of the
merged Excel data). Wave B: toggle the 9-step credit-file checklist, recording
each change to the activity journal (mirrors the Excel MarkChecklistRowComplete /
SubmitChecklist + WriteToJournal).
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.crm import ChecklistProgress, FacilityChecklist, CHECKLIST_STEPS, JournalEntry, CustomTask, CustomerProfile, CustomerNote, Attachment
from app.services import attachments as attachments_store
from app.models.guarantor import Guarantor
from app.models.profile_entities import MortgagedProperty, FixedDeposit, Partner
from app.models.customer import Customer
from app.models.facility import Facility, FacilityType
from app.services.checklist import seed_facility_checklist, HOURGLASS
from app.services.completeness import recompute_completeness
from app.routers.auth import require_editor, require_admin

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
    tid = f"T-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}"
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
    if "cheque" in u and ("disc" in u or "discount" in u):
        return FacilityType.CHEQUE_DISCOUNTING
    if "trust" in u or u in ("tr", "t/r"):
        return FacilityType.TRUST_RECEIPT
    if "loan" in u:
        return FacilityType.LOAN
    if "usance" in u:
        return FacilityType.LC_USANCE
    if "sight" in u:
        return FacilityType.LC_SIGHT
    if u == "lc" or "letter of credit" in u:
        return FacilityType.LC
    if u == "log" or "letter of guarantee" in u:
        return FacilityType.LOG
    if u == "lg" or "guarantee" in u:
        return FacilityType.LG
    return FacilityType.OTHER


class FacilityCreate(BaseModel):
    facility_type: str = "loan"
    amount: float = Field(..., ge=0)
    currency: str = "AED"
    name: str = ""  # facility / offer-letter reference
    loan_type: str = ""       # Personal / Commercial / Staff
    installments: str = ""


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
    fid = f"F-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}"
    f = Facility(
        id=fid, customer_id=cid, name=(payload.name or "")[:200], amount=payload.amount,
        currency=(payload.currency or "AED")[:3], facility_type=_facility_type(payload.facility_type),
        loan_type=(payload.loan_type or "")[:30] or None,
        installments=(payload.installments or "")[:10] or None,
        risk_rating="medium", is_deleted=False,
    )
    db.add(f)
    # A24: stamp an hourglass on every step of the new facility's own checklist.
    await seed_facility_checklist(db, account_no, fid, getattr(user, "username", "") or "")
    await db.commit()
    return {
        "id": f.id, "name": f.name, "amount": float(f.amount or 0),
        "currency": f.currency, "facility_type": f.facility_type.value,
        "loan_type": f.loan_type, "installments": f.installments,
        "status": "active", "outstanding": 0,
    }


def _fc_dict(fc: FacilityChecklist) -> dict:
    return {
        "id": fc.id, "account_no": fc.account_no, "facility_id": fc.facility_id,
        "total": fc.total, "last_action": fc.last_action, "last_user": fc.last_user,
        **{f"item{i}": getattr(fc, f"item{i}", "") for i in range(1, 10)},
    }


@router.patch("/facility-checklist/{facility_id}")
async def toggle_facility_checklist(
    facility_id: str,
    payload: StepToggle,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Mark a step done/pending on a FACILITY's own checklist (creates it, seeded
    with hourglasses, if it doesn't exist yet)."""
    fid = (facility_id or "").strip()
    fc = (
        await db.execute(select(FacilityChecklist).where(FacilityChecklist.facility_id == fid))
    ).scalar_one_or_none()
    if fc is None:
        fac = (await db.execute(select(Facility).where(Facility.id == fid))).scalar_one_or_none()
        account_no = ""
        if fac is not None:
            account_no = (
                await db.execute(select(Customer.account_no).where(Customer.id == fac.customer_id))
            ).scalar_one_or_none() or ""
        fc = await seed_facility_checklist(db, account_no, fid, getattr(user, "username", "") or "")
    setattr(fc, f"item{payload.step}", "✓" if payload.done else HOURGLASS)
    fc.total = str(sum(1 for i in range(1, 10) if _is_done(getattr(fc, f"item{i}", ""))))
    fc.last_action = date.today().isoformat()
    fc.last_user = getattr(user, "username", "") or ""
    db.add(JournalEntry(
        id="J-" + uuid.uuid4().hex[:18],
        account_no=fc.account_no,
        item=f"{CHECKLIST_STEPS[payload.step - 1]} (facility {fid})",
        status="✓" if payload.done else HOURGLASS,
        action="Submit" if payload.done else "Unmark",
        source="Facility Checklist",
        date=date.today().isoformat(),
        user=getattr(user, "username", "") or "",
    ))
    await db.commit()
    return _fc_dict(fc)


# ---------------------------------------------------------------------------
# Customer profile / KYC editing
# ---------------------------------------------------------------------------
# Editable profile/KYC fields. Number + issue + expiry + remarks (+ sub-fields:
# passport nationality, Emirates-ID golden flag, visa type, tenancy address) for
# each of the 5 identity documents. Doc-path columns are set by the upload
# feature (Phase 3), not here.
_KYC_FIELDS = [
    "business_type", "rating", "customer_status",
    "trade_license_no", "trade_license_issue", "trade_license_expiry", "trade_license_remarks",
    "passport_no", "passport_issue", "passport_expiry", "passport_nationality", "passport_remarks",
    "emirates_id_no", "emirates_id_issue", "emirates_id_expiry", "emirates_id_remarks", "emirates_id_golden",
    "visa_no", "visa_issue", "visa_expiry", "visa_type",
    "tenancy_no", "tenancy_issue", "tenancy_expiry", "tenancy_address",
]


class ProfileUpdate(BaseModel):
    business_type: Optional[str] = None
    rating: Optional[str] = None
    customer_status: Optional[str] = None
    trade_license_no: Optional[str] = None
    trade_license_issue: Optional[str] = None
    trade_license_expiry: Optional[str] = None
    trade_license_remarks: Optional[str] = None
    passport_no: Optional[str] = None
    passport_issue: Optional[str] = None
    passport_expiry: Optional[str] = None
    passport_nationality: Optional[str] = None
    passport_remarks: Optional[str] = None
    emirates_id_no: Optional[str] = None
    emirates_id_issue: Optional[str] = None
    emirates_id_expiry: Optional[str] = None
    emirates_id_remarks: Optional[str] = None
    emirates_id_golden: Optional[str] = None
    visa_no: Optional[str] = None
    visa_issue: Optional[str] = None
    visa_expiry: Optional[str] = None
    visa_type: Optional[str] = None
    tenancy_no: Optional[str] = None
    tenancy_issue: Optional[str] = None
    tenancy_expiry: Optional[str] = None
    tenancy_address: Optional[str] = None


@router.patch("/profile/{account_no}")
async def update_profile(
    account_no: str,
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Edit a customer's profile / KYC fields (creates the profile if missing)."""
    cp = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == account_no))
    ).scalar_one_or_none()
    if cp is None:
        cp = CustomerProfile(account_no=account_no)
        db.add(cp)
    cols = CustomerProfile.__table__.columns
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None and k in _KYC_FIELDS:
            maxlen = getattr(getattr(cols.get(k), "type", None), "length", None)
            s = str(v)
            setattr(cp, k, s[:maxlen] if maxlen else s)
    cp.last_updated = date.today().isoformat()
    cp.updated_by = getattr(user, "username", "") or ""
    # Recompute completeness so the stored % reflects the edit (A25).
    await recompute_completeness(db, account_no)
    await db.commit()
    result = {k: getattr(cp, k, None) for k in _KYC_FIELDS}
    result["profile_completeness"] = cp.profile_completeness
    return result


@router.get("/completeness/{account_no}")
async def get_completeness(
    account_no: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Completeness % + the list of fields still missing (Excel ShowMissingFields)."""
    result = await recompute_completeness(db, account_no)
    await db.commit()
    return result


# ---------------------------------------------------------------------------
# Data-merge: manual trigger + status (admin) — so the legacy Excel data can be
# (re)merged on demand and verified, without waiting for a restart.
# ---------------------------------------------------------------------------
@router.api_route("/run-merge", methods=["GET", "POST"])
async def run_merge(user=Depends(require_admin)):
    """Run the legacy-data merge now and return a per-step report.

    Accepts GET too, so an admin can trigger + inspect it straight from the
    browser address bar (handy when AUTH_DISABLED is on).
    """
    from app.services.data_merge import run_data_merge
    report = await run_data_merge()
    return {"ok": True, "report": report}


@router.get("/merge-status")
async def merge_status(db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """Row counts of the merged CRM tables (to verify the merge landed)."""
    from sqlalchemy import func
    from app.models.crm import Attachment, JournalEntry
    from app.models.security import Security

    out = {}
    checks = {
        "guarantors": Guarantor, "customer_profiles": CustomerProfile,
        "checklist_progress": ChecklistProgress, "custom_tasks": CustomTask,
        "attachments": Attachment, "journal_entries": JournalEntry,
        "securities": Security,
    }
    for label, model in checks.items():
        try:
            out[label] = (await db.execute(select(func.count()).select_from(model))).scalar() or 0
        except Exception as exc:
            out[label] = f"error: {str(exc)[:80]}"
    # facilities with a real (non-zero) amount = the fill worked
    try:
        out["facilities_total"] = (await db.execute(select(func.count()).select_from(Facility).where(Facility.is_deleted == False))).scalar() or 0
        out["facilities_with_amount"] = (await db.execute(select(func.count()).select_from(Facility).where(Facility.is_deleted == False, Facility.amount > 0))).scalar() or 0
    except Exception as exc:
        out["facilities"] = f"error: {str(exc)[:80]}"
    return out


# ---------------------------------------------------------------------------
# Email a credit digest for one customer (the Excel DailyReport /
# SendUnsentNotesToEmail feature). Requires SMTP_* configured on the server.
# ---------------------------------------------------------------------------
class EmailSummaryRequest(BaseModel):
    to: str = Field(..., min_length=3, max_length=200)


def _num(v) -> float:
    try:
        return float(str(v or "0").replace(",", "").replace("/-", "").strip() or 0)
    except Exception:
        return 0.0


@router.post("/email-summary/{account_no}")
async def email_summary(
    account_no: str,
    payload: EmailSummaryRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Email a concise credit digest (exposure, facilities, securities, open tasks)
    for one customer to a recipient."""
    from app.services.email import send_email, smtp_configured

    if not smtp_configured():
        raise HTTPException(
            status_code=400,
            detail="SMTP is not configured. Set SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD on the server.",
        )
    acc = (account_no or "").strip()
    cust = (
        await db.execute(
            select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False)
        )
    ).scalar_one_or_none()
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    facs = (
        await db.execute(
            select(Facility).where(Facility.customer_id == cust.id, Facility.is_deleted == False)
        )
    ).scalars().all()
    guars = (
        await db.execute(
            select(Guarantor).where(Guarantor.account_no == acc, Guarantor.is_deleted == False)
        )
    ).scalars().all()
    tasks = (await db.execute(select(CustomTask).where(CustomTask.account_no == acc))).scalars().all()

    exposure = sum(_num(f.amount) for f in facs)
    cheque_total = sum(_num(g.cheque_amount) for g in guars if g.cheque_amount)
    cheque_count = len([g for g in guars if g.cheque_no])
    open_tasks = [
        t for t in tasks
        if str(getattr(t, "status", "") or "").strip().lower() not in ("done", "completed", "closed")
    ]

    def _ev(x):
        return getattr(x, "value", x)

    lines = [
        f"Credit File Summary — {cust.name} ({acc})",
        f"Branch: {cust.branch or '-'}    Type: {_ev(cust.account_type)}",
        "",
        f"Total exposure : AED {exposure:,.0f}    |    Facilities: {len(facs)}",
        f"Security cheques: {cheque_count} (AED {cheque_total:,.0f})    |    Guarantors: {len(guars)}",
        "",
        "Facilities:",
    ]
    for f in facs[:25]:
        lines.append(
            f"  - {f.name or f.id}: {_ev(f.facility_type)} AED {_num(f.amount):,.0f} [{_ev(f.status)}]"
        )
    if not facs:
        lines.append("  (none)")
    if open_tasks:
        lines += ["", f"Open tasks ({len(open_tasks)}):"]
        for t in open_tasks[:25]:
            lines.append(f"  - {t.task_name or '-'} (due {t.followup_date or '-'})")
    lines += [
        "",
        f"Generated by ALLIN1 — Bank Saderat Iran (UAE) on {datetime.utcnow():%Y-%m-%d %H:%M} UTC",
        f"Requested by: {getattr(user, 'username', None) or getattr(user, 'email', None) or 'user'}",
    ]
    body = "\n".join(lines)
    ok, msg = await send_email(payload.to, f"Credit Summary — {cust.name} ({acc})", body)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"ok": True, "message": f"Summary emailed to {payload.to}"}


# ---------------------------------------------------------------------------
# Offer-letter prefill: map an account's profile + facility to the Word
# template's placeholders, so the Offer Letter form fills itself from the file.
# ---------------------------------------------------------------------------
_FTYPE_LABEL = {
    "overdraft": "Overdraft", "loan": "Loan", "lc": "Letter of Credit",
    "lg": "Letter of Guarantee", "other": "Credit Facility",
}


@router.get("/offer-letter-data/{account_no}")
async def offer_letter_data(
    account_no: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Best-effort prefill for the Offer Letter from the account's profile +
    largest active facility. Unknown fields come back empty for the user to fill."""
    acc = (account_no or "").strip()
    cust = (
        await db.execute(
            select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False)
        )
    ).scalar_one_or_none()
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    prof = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
    ).scalar_one_or_none()
    pdata = {}
    if prof is not None and prof.data_json:
        try:
            pdata = json.loads(prof.data_json)
        except Exception:
            pdata = {}

    def pget(*keys):
        for k in keys:
            for kk in (k, k.replace(" ", ""), k.lower()):
                v = pdata.get(kk)
                if v not in (None, "", "-"):
                    return str(v).strip()
        return ""

    facs = (
        await db.execute(
            select(Facility).where(Facility.customer_id == cust.id, Facility.is_deleted == False)
        )
    ).scalars().all()
    fac = max(facs, key=lambda f: float(f.amount or 0), default=None) if facs else None
    ftype = (getattr(fac.facility_type, "value", fac.facility_type) if fac else "") or ""
    rate = None
    if fac is not None and fac.interest_rate is not None:
        rate = f"{float(fac.interest_rate):g}% p.a."
    return {
        "CompanyName": cust.name or "",
        "AccountNumber": acc,
        "POBox": pget("POBox", "PO Box", "P.O.Box", "POBOX", "Po Box"),
        "CityCountry": pget("CityCountry", "City", "Emirate") or "DUBAI - U.A.E.",
        "Branch": cust.branch or "",
        "Rating": (getattr(prof, "rating", "") or "") if prof else "",
        "BusinessType": ((getattr(prof, "business_type", "") or "") if prof else "") or pget("BusinessType"),
        "FacilityType": _FTYPE_LABEL.get(ftype, "Overdraft"),
        "CreditLimit": (f"{float(fac.amount):,.0f}" if fac and fac.amount else ""),
        "InterestRate": rate or "",
        "ExpiryDate": (str(fac.expiry_date) if fac and getattr(fac, "expiry_date", None) else ""),
        "ValidUntil": (str(fac.expiry_date) if fac and getattr(fac, "expiry_date", None) else ""),
        "facilities_count": len(facs),
    }


# ---------------------------------------------------------------------------
# Notes (free-text notes / reminders per customer)
# ---------------------------------------------------------------------------
class NoteCreate(BaseModel):
    title: str = ""
    content: str = Field(..., min_length=1)
    category: str = "General"
    priority: str = "Medium"
    reminder_date: str = ""


@router.post("/notes/{account_no}")
async def add_note(
    account_no: str,
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Add a note / reminder to a customer."""
    nid = f"N-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}"
    n = CustomerNote(
        id=nid, account_no=account_no, title=(payload.title or "")[:200], content=payload.content,
        category=(payload.category or "General")[:40], priority=(payload.priority or "Medium")[:20],
        created_by=getattr(user, "username", "") or "", created_date=date.today().isoformat(),
        reminder_date=(payload.reminder_date or "")[:30],
    )
    db.add(n)
    await db.commit()
    return {
        "id": n.id, "account_no": n.account_no, "title": n.title, "content": n.content,
        "category": n.category, "priority": n.priority, "created_by": n.created_by,
        "created_date": n.created_date, "reminder_date": n.reminder_date,
    }


# ===========================================================================
# Profile child records — mortgaged properties, fixed deposits, partners.
# Per-customer (account_no-keyed) STRUCTURED data the legacy PF_* profile held
# and requirement A12 (sheet «پرامپت») asks to capture. Each supports
# add / edit / soft-delete; they are listed by GET /api/customers/{id}/detail.
# ===========================================================================
from decimal import Decimal

# Columns that hold money/amounts (assigned as-is; everything else is a string
# truncated to its column width).
_NUMERIC_CHILD_FIELDS = {"valuation", "mortgage_amount", "amount"}


def _new_child_id(prefix: str, account_no: str) -> str:
    return f"{prefix}-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}"


def _child_dict(obj) -> dict:
    """JSON-friendly view of a child row (Decimal -> float, drop created_at)."""
    out = {}
    for col in obj.__table__.columns:
        if col.name == "created_at":
            continue
        v = getattr(obj, col.name)
        out[col.name] = float(v) if isinstance(v, Decimal) else v
    return out


def _apply_child_fields(obj, data: dict, allowed: set) -> None:
    """Assign provided (exclude_unset) fields: numerics as-is, strings truncated
    to the column width so an over-long value can never overflow the column."""
    cols = obj.__table__.columns
    for k, v in data.items():
        if k not in allowed or v is None:
            continue
        if k in _NUMERIC_CHILD_FIELDS:
            setattr(obj, k, v)
            continue
        col = cols.get(k)
        maxlen = getattr(getattr(col, "type", None), "length", None) if col is not None else None
        s = str(v)
        setattr(obj, k, s[:maxlen] if maxlen else s)


async def _add_child(db, model, prefix, account_no, data, allowed, user):
    obj = model(
        id=_new_child_id(prefix, account_no),
        account_no=account_no,
        date_added=date.today().isoformat(),
        created_by=getattr(user, "username", "") or "",
    )
    _apply_child_fields(obj, data, allowed)
    db.add(obj)
    await db.commit()
    return _child_dict(obj)


async def _update_child(db, model, item_id, data, allowed):
    obj = (await db.execute(select(model).where(model.id == item_id))).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found")
    _apply_child_fields(obj, data, allowed)
    await db.commit()
    return _child_dict(obj)


async def _delete_child(db, model, item_id):
    obj = (await db.execute(select(model).where(model.id == item_id))).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found")
    obj.is_deleted = True
    await db.commit()
    return {"ok": True, "id": item_id, "deleted": True}


# ---- Mortgaged properties (A12) ----
_PROPERTY_FIELDS = {
    "country", "plate_no", "mortgage_deed_no", "city", "address", "prop_type",
    "building_age", "land_area", "cnbc", "valuation", "valuation_currency",
    "insurance_expiry", "insurance_no", "last_valuation_date", "mortgage_date",
    "mortgage_amount", "remarks",
}


class PropertyCreate(BaseModel):
    country: str = ""
    plate_no: str = ""
    mortgage_deed_no: str = ""
    city: str = ""
    address: str = ""
    prop_type: str = ""
    building_age: str = ""
    land_area: str = ""
    cnbc: str = ""
    valuation: Optional[float] = None
    valuation_currency: str = "AED"
    insurance_expiry: str = ""
    insurance_no: str = ""
    last_valuation_date: str = ""
    mortgage_date: str = ""
    mortgage_amount: Optional[float] = None
    remarks: str = ""


class PropertyUpdate(BaseModel):
    country: Optional[str] = None
    plate_no: Optional[str] = None
    mortgage_deed_no: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    prop_type: Optional[str] = None
    building_age: Optional[str] = None
    land_area: Optional[str] = None
    cnbc: Optional[str] = None
    valuation: Optional[float] = None
    valuation_currency: Optional[str] = None
    insurance_expiry: Optional[str] = None
    insurance_no: Optional[str] = None
    last_valuation_date: Optional[str] = None
    mortgage_date: Optional[str] = None
    mortgage_amount: Optional[float] = None
    remarks: Optional[str] = None


@router.post("/properties/{account_no}")
async def add_property(
    account_no: str, payload: PropertyCreate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Add a mortgaged property to a customer's profile."""
    return await _add_child(
        db, MortgagedProperty, "PROP", account_no,
        payload.model_dump(exclude_unset=True), _PROPERTY_FIELDS, user,
    )


@router.patch("/properties/{item_id}")
async def update_property(
    item_id: str, payload: PropertyUpdate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Edit a mortgaged property."""
    return await _update_child(
        db, MortgagedProperty, item_id, payload.model_dump(exclude_unset=True), _PROPERTY_FIELDS,
    )


@router.delete("/properties/{item_id}")
async def delete_property(
    item_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Remove (soft-delete) a mortgaged property."""
    return await _delete_child(db, MortgagedProperty, item_id)


# ---- Fixed deposits (A12) ----
_FD_FIELDS = {"fd_number", "amount", "currency", "open_date", "maturity_date", "rate", "remarks"}


class FixedDepositCreate(BaseModel):
    fd_number: str = ""
    amount: Optional[float] = None
    currency: str = "AED"
    open_date: str = ""
    maturity_date: str = ""
    rate: str = ""
    remarks: str = ""


class FixedDepositUpdate(BaseModel):
    fd_number: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    open_date: Optional[str] = None
    maturity_date: Optional[str] = None
    rate: Optional[str] = None
    remarks: Optional[str] = None


@router.post("/fixed-deposits/{account_no}")
async def add_fixed_deposit(
    account_no: str, payload: FixedDepositCreate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Add a fixed deposit to a customer's profile."""
    return await _add_child(
        db, FixedDeposit, "FD", account_no,
        payload.model_dump(exclude_unset=True), _FD_FIELDS, user,
    )


@router.patch("/fixed-deposits/{item_id}")
async def update_fixed_deposit(
    item_id: str, payload: FixedDepositUpdate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Edit a fixed deposit."""
    return await _update_child(
        db, FixedDeposit, item_id, payload.model_dump(exclude_unset=True), _FD_FIELDS,
    )


@router.delete("/fixed-deposits/{item_id}")
async def delete_fixed_deposit(
    item_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Remove (soft-delete) a fixed deposit."""
    return await _delete_child(db, FixedDeposit, item_id)


# ---- Partners / shareholders ----
_PARTNER_FIELDS = {"name", "nationality", "share", "remarks"}


class PartnerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    nationality: str = ""
    share: str = ""
    remarks: str = ""


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    nationality: Optional[str] = None
    share: Optional[str] = None
    remarks: Optional[str] = None


@router.post("/partners/{account_no}")
async def add_partner(
    account_no: str, payload: PartnerCreate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Add a partner / shareholder to a customer's profile."""
    return await _add_child(
        db, Partner, "PTNR", account_no,
        payload.model_dump(exclude_unset=True), _PARTNER_FIELDS, user,
    )


@router.patch("/partners/{item_id}")
async def update_partner(
    item_id: str, payload: PartnerUpdate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Edit a partner / shareholder."""
    return await _update_child(
        db, Partner, item_id, payload.model_dump(exclude_unset=True), _PARTNER_FIELDS,
    )


@router.delete("/partners/{item_id}")
async def delete_partner(
    item_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Remove (soft-delete) a partner / shareholder."""
    return await _delete_child(db, Partner, item_id)


# ===========================================================================
# Document attachments — real per-row / per-checklist upload + download (A10/A15).
# The file bytes are stored on disk (services.attachments); the row records the
# metadata, scoped to a facility + checklist row (or shared across checklists).
# ===========================================================================
def _attachment_dict(a: Attachment) -> dict:
    return {
        "id": a.id, "account_no": a.account_no, "facility_id": a.facility_id,
        "row_index": a.row_index, "file_name": a.file_name, "original_name": a.original_name,
        "file_size": a.file_size, "upload_date": a.upload_date, "uploaded_by": a.uploaded_by,
        "is_shared": a.is_shared, "notes": a.notes,
    }


@router.post("/attachments/{account_no}")
async def upload_attachment(
    account_no: str,
    file: UploadFile = File(...),
    facility_id: str = Form(""),
    row_index: str = Form(""),
    is_shared: bool = Form(False),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Upload a document, store it on disk under the customer/facility folder and
    record its metadata (scoped to a facility + checklist row, or shared)."""
    rel, size, stored = await attachments_store.save_upload(account_no, facility_id, file)
    aid = f"A-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}"
    a = Attachment(
        id=aid, account_no=account_no, facility_id=(facility_id or "")[:60],
        row_index=(row_index or "")[:10], file_name=stored[:255],
        original_name=(file.filename or stored)[:255], file_path=rel,
        file_size=str(size), upload_date=date.today().isoformat(),
        uploaded_by=getattr(user, "username", "") or "",
        is_shared="1" if is_shared else "0", notes=notes or "",
    )
    db.add(a)
    await db.commit()
    return _attachment_dict(a)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Stream a stored document back so it actually opens again (fixes A15)."""
    a = (await db.execute(select(Attachment).where(Attachment.id == attachment_id))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = attachments_store.resolve(a.file_path or "")
    if path is None:
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(str(path), filename=a.original_name or a.file_name or "document")


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Remove an attachment record and its stored file."""
    a = (await db.execute(select(Attachment).where(Attachment.id == attachment_id))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = attachments_store.resolve(a.file_path or "")
    if path is not None:
        try:
            path.unlink()
        except OSError:
            pass
    await db.delete(a)
    await db.commit()
    return {"ok": True, "id": attachment_id, "deleted": True}
