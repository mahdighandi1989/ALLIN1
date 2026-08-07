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

import re

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.crm import ChecklistProgress, FacilityChecklist, CHECKLIST_STEPS, JournalEntry, CustomTask, CustomerProfile, CustomerNote, Attachment
from app.services import attachments as attachments_store
from app.models.guarantor import Guarantor
from app.models.credit_review import CreditReview
from app.models.profile_entities import MortgagedProperty, FixedDeposit, Partner, PropertyEvent
from app.models.customer import Customer
from app.models.facility import Facility, FacilityType
from app.services.checklist import seed_facility_checklist, HOURGLASS
from app.services.completeness import recompute_completeness
from app.routers.auth import require_editor, require_admin, get_current_active_user

router = APIRouter(tags=["crm"])


def _content_disposition(kind: str, filename: str) -> str:
    """RFC 6266 header with the user-supplied name made header-safe.

    The stored original_name is uploader-controlled: a double quote breaks out
    of the quoted parameter and a CR/LF aborts the whole response at the ASGI
    layer. ASCII-quote-escape for the legacy parameter + RFC 5987 UTF-8
    filename* so non-Latin (Persian/Arabic) names survive.
    """
    from urllib.parse import quote

    safe = (filename or "document").replace("\r", " ").replace("\n", " ")
    ascii_fallback = safe.encode("ascii", "replace").decode("ascii").replace('"', "'")
    return (
        f'{kind}; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(safe, safe='')}"
    )



async def _audit(db, user, *, action, entity_type, account_no, entity_id=None, detail=None):
    """Record a customer-scoped action in the activity/audit log (best-effort)."""
    from app.services.audit import record_audit
    await record_audit(
        action=action, entity_type=entity_type, entity_id=entity_id,
        account_no=account_no, detail=detail, user=user, request=None, db=db,
    )


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
    await _audit(db, user, action="update", entity_type="checklist", account_no=account_no,
                 detail=f"{'تکمیلِ' if payload.done else 'لغوِ'} مرحلهٔ «{step_name}»")
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
    await _audit(db, user, action="create", entity_type="task", account_no=account_no, entity_id=tid,
                 detail=f"تسکِ پیگیری: {payload.task_name}")
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
    deactivated = payload.is_active is not None and payload.is_active.strip() in ("0", "false", "")
    completed = payload.status is not None and payload.status.strip().lower() in ("done", "completed", "✓")
    await _audit(db, user, action="delete" if deactivated else "update", entity_type="task",
                 account_no=t.account_no, entity_id=t.id,
                 detail=("حذفِ تسک" if deactivated else ("تکمیلِ تسک" if completed else "به‌روزرسانیِ تسک")) + f": {t.task_name}")
    return _task_dict(t)


# ---------------------------------------------------------------------------
# Guarantors (add a guarantor + security cheque to a customer)
# ---------------------------------------------------------------------------
def _acct_core(acct: str) -> str:
    """The stable 6-digit core of an account number, ignoring branch prefix and
    suffix formatting: "2624-131757-006" → "131757", "131757" → "131757".

    UAE account rows are stored inconsistently across the securities-list imports
    (some full "branch-core-suffix", some bare core), which is what makes the same
    guarantor look like two people. When exactly one 6-digit group exists we take
    it; otherwise (ambiguous) we return "" and fall back to strict matching."""
    import re

    groups = re.findall(r"\d{6}", str(acct or ""))
    return groups[0] if len(groups) == 1 else ""


def _name_tokens(name: str) -> set:
    """Alphanumeric name tokens, upper-cased, honorifics/filler dropped."""
    import re

    drop = {"MR", "MRS", "MS", "MISS", "M/S", "AL", "EL", "BIN", "BINT", "THE"}
    toks = re.findall(r"[A-Za-z0-9]+", str(name or "").upper())
    return {t for t in toks if t not in drop and len(t) > 1}


def _name_similar(a: set, b: set) -> bool:
    """Same person heuristic: strong token overlap OR one is a subset of the other
    (covers "SALWA MOHD YOUSIF JUMA" vs "SALWA MOHAMED YOUSIF JUMA AL MAAZMI").
    Deliberately conservative — requires ≥2 shared tokens (or subset) so unrelated
    people never merge."""
    if not a or not b:
        return False
    shared = a & b
    if a <= b or b <= a:
        return len(shared) >= 2
    smaller = min(len(a), len(b))
    return len(shared) >= max(2, smaller - 1)


class GuarantorCreate(BaseModel):
    guarantor_name: str = Field(..., min_length=1, max_length=200)
    guarantor_account: str = ""
    cheque_no: str = ""
    cheque_amount: Optional[float] = None
    issuing_bank: str = "BSI"
    pim_ref: str = ""
    facility_id: str = ""
    branch: str = ""
    national_id: str = ""
    id: str = ""  # when set, update that record (else match by account+cheque_no)


def _guarantor_out(g) -> dict:
    """One JSON shape for a guarantor / security cheque, reused by list + upsert."""
    return {
        "id": g.id, "account_no": g.account_no, "customer_name": g.customer_name,
        "guarantor_name": g.guarantor_name, "guarantor_account": g.guarantor_account,
        "cheque_no": g.cheque_no,
        "cheque_amount": float(g.cheque_amount) if g.cheque_amount is not None else None,
        "issuing_bank": g.issuing_bank, "pim_ref": g.pim_ref, "national_id": g.national_id,
        "facility_id": g.facility_id, "branch": g.branch, "date_added": g.date_added,
        # v95 — release (سند برگشتی) status
        "released": (g.released or "") == "1",
        "released_date": g.released_date, "release_note": g.release_note,
    }


class ChequeReleaseIn(BaseModel):
    cheque_no: str = ""
    facility_id: str = ""
    settled_facility: str = ""
    date: str = ""            # DD/MM/YYYY from the voucher form
    note: str = ""


@router.post("/guarantors/{account_no}/release")
async def release_security_cheque(
    account_no: str,
    payload: ChequeReleaseIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """v95 — the REVERSAL voucher's write path: mark the account's security
    cheque(s) as RETURNED (خروج‌خورده) when their facility settles. Matches by
    cheque_no (plus facility when given); nothing is deleted — the record keeps
    living under the profile with released/date/note stamped, and the release
    lands in the account's activity log (the customer page's «لاگِ کارها»)."""
    from datetime import date as _date

    chq = (payload.cheque_no or "").strip()
    fac = (payload.facility_id or "").strip()
    if not chq:
        raise HTTPException(status_code=422, detail="شمارهٔ چک برای ثبتِ خروج لازم است.")
    q = select(Guarantor).where(
        Guarantor.account_no == account_no,
        Guarantor.cheque_no == chq,
        Guarantor.is_deleted == False,  # noqa: E712
    )
    if fac:
        q = q.where(Guarantor.facility_id == fac)
    rows = (await db.execute(q)).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="چکی با این شماره (و تسهیلات) برای این حساب ثبت نشده است.")
    when = (payload.date or "").strip() or _date.today().strftime("%d/%m/%Y")
    settled = (payload.settled_facility or "").strip()
    note = (payload.note or "").strip()
    # v97 — the settlement description is the user's own words, stored VERBATIM
    # (no automatic «LOAN SETTLED» prefix — that was the sample workbook's text).
    stamp = " — ".join(x for x in [
        "SECURITY CHQ REVERSAL",
        settled,
        note,
    ] if x)[:300]
    n_new = n_already = 0
    for g in rows:
        if (g.released or "") == "1":
            n_already += 1
        else:
            n_new += 1
        g.released = "1"
        g.released_date = when
        g.release_note = stamp
    await db.commit()
    await _audit(db, user, action="release", entity_type="security_cheque",
                 account_no=account_no, entity_id=rows[0].id,
                 detail=f"خروجِ چکِ ضمانتی {chq}"
                        + (f" (تسهیلات {fac})" if fac else "")
                        + (f" — {settled}" if settled else "")
                        + f" — تاریخ {when} (سندِ برگشتی)")
    return {"ok": True, "released": n_new, "already_released": n_already,
            "guarantors": [_guarantor_out(g) for g in rows]}


@router.get("/guarantors/{account_no}")
async def list_guarantors(
    account_no: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """Every security cheque / guarantor recorded for an account — the single
    source of truth shared by the customer-detail page and the Per-Contra voucher
    form (so both read/write the same records, no scattered duplicates)."""
    rows = (
        await db.execute(
            select(Guarantor)
            .where(Guarantor.account_no == account_no, Guarantor.is_deleted == False)  # noqa: E712
            .order_by(Guarantor.date_added.desc())
        )
    ).scalars().all()
    return [_guarantor_out(g) for g in rows]


@router.post("/guarantors/{account_no}")
async def add_guarantor(
    account_no: str,
    payload: GuarantorCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Create OR update a guarantor / security cheque (idempotent upsert).

    Matches an existing record by explicit ``id`` or by (account_no, cheque_no),
    so the same cheque saved from the voucher form and from the customer page
    stays ONE record instead of scattering duplicate islands. Pins to a facility
    and auto-stubs the owning + guarantor accounts.
    """
    from app.services.customer_link import ensure_customer

    customer = await ensure_customer(db, account_no, None)
    if (payload.guarantor_account or "").strip():
        await ensure_customer(db, payload.guarantor_account, payload.guarantor_name)

    g = None
    if (payload.id or "").strip():
        g = (await db.execute(select(Guarantor).where(Guarantor.id == payload.id.strip()))).scalar_one_or_none()
    if g is None and (payload.cheque_no or "").strip():
        g = (
            await db.execute(
                select(Guarantor).where(
                    Guarantor.account_no == account_no,
                    Guarantor.cheque_no == payload.cheque_no.strip(),
                    Guarantor.is_deleted == False,  # noqa: E712
                )
            )
        ).scalar_one_or_none()
    if g is None and not (payload.cheque_no or "").strip():
        # No cheque to key on (e.g. saved from the Offer Letter): match by the
        # guarantor's name (case-insensitive; same account when both sides have
        # one) so re-saving the same person stays ONE record, not a duplicate.
        name_key = " ".join(payload.guarantor_name.split()).lower()
        acct_key = (payload.guarantor_account or "").strip()
        candidates = (
            await db.execute(
                select(Guarantor).where(
                    Guarantor.account_no == account_no,
                    Guarantor.is_deleted == False,  # noqa: E712
                )
            )
        ).scalars().all()
        matches = [
            c for c in candidates
            if " ".join((c.guarantor_name or "").split()).lower() == name_key
        ]
        if acct_key:
            with_acct = [c for c in matches if (c.guarantor_account or "").strip() in ("", acct_key)]
            matches = with_acct
        # Conservative second pass (forward-fix for the near-duplicate the owner
        # reported: "131757" vs "2624-131757-006", "MOHD" vs "MOHAMED"). Only
        # matches when the 6-digit ACCOUNT CORE is identical AND the names share
        # a strong token overlap — so genuinely different guarantors never merge.
        if not matches and acct_key:
            core = _acct_core(acct_key)
            if core:
                new_tokens = _name_tokens(payload.guarantor_name)
                for c in candidates:
                    if _acct_core(c.guarantor_account or "") != core:
                        continue
                    if _name_similar(new_tokens, _name_tokens(c.guarantor_name or "")):
                        matches = [c]
                        break
        if matches:
            g = matches[0]
    created = g is None
    if g is None:
        gid = f"G-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:2]}"
        g = Guarantor(
            id=gid, account_no=account_no, date_added=date.today().isoformat(),
            created_by=getattr(user, "username", "") or "",
        )
        db.add(g)

    # Apply the submitted values (blank optional fields keep the existing value).
    g.guarantor_name = payload.guarantor_name[:200]
    if (payload.cheque_no or "").strip():
        # A blank cheque_no keeps the stored one (per the contract above) — the
        # old unconditional assignment wiped it on any cheque-less re-save.
        g.cheque_no = payload.cheque_no.strip()[:50]
    if payload.cheque_amount is not None:
        g.cheque_amount = payload.cheque_amount
    g.issuing_bank = (payload.issuing_bank or "BSI")[:50]
    if (payload.guarantor_account or "").strip():
        g.guarantor_account = payload.guarantor_account[:50]
    if (payload.pim_ref or "").strip():
        g.pim_ref = payload.pim_ref[:80]
    if (payload.facility_id or "").strip():
        g.facility_id = payload.facility_id[:60]
    if (payload.branch or "").strip():
        g.branch = payload.branch[:20]
    if (payload.national_id or "").strip():
        g.national_id = payload.national_id.strip()[:40]
    if customer and getattr(customer, "name", None) and not g.customer_name:
        g.customer_name = customer.name

    await db.commit()
    await _audit(db, user, action="create" if created else "update", entity_type="guarantor",
                 account_no=account_no, entity_id=g.id,
                 detail=f"{'افزودنِ' if created else 'ویرایشِ'} ضامن «{g.guarantor_name}»"
                        + (f" — چک {g.cheque_no}" if g.cheque_no else ""))
    return {**_guarantor_out(g), "created": created}


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
    await _audit(db, user, action="create", entity_type="facility", account_no=account_no, entity_id=fid,
                 detail=f"افزودنِ تسهیلات «{f.name or f.facility_type.value}» — {f.currency} {float(f.amount or 0):,.0f}")
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
    "grade", "call_report", "previous_files", "undertaking_from",
]


class ProfileUpdate(BaseModel):
    business_type: Optional[str] = None
    rating: Optional[str] = None
    customer_status: Optional[str] = None
    national_id: Optional[str] = None
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
    grade: Optional[str] = None
    call_report: Optional[str] = None
    previous_files: Optional[str] = None
    undertaking_from: Optional[str] = None


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
    changed = [k for k in data if k in _KYC_FIELDS and data[k] is not None]
    await _audit(db, user, action="update", entity_type="profile", account_no=account_no,
                 detail="ویرایشِ پروفایل/مدارک" + (f" ({len(changed)} فیلد)" if changed else ""))
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


@router.api_route("/run-expiry-scan", methods=["GET", "POST"])
async def run_expiry_scan_endpoint(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Scan facilities + KYC documents and raise/refresh expiry alert tasks
    (the Excel CheckAllExpiriesAndCreateAlerts). Consumes the
    `expiry_warning_days` setting. Accepts GET so an admin can run it from the
    browser address bar too."""
    from app.services.expiry import run_expiry_scan
    return await run_expiry_scan(db)


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
def _non_facility_text(text: str) -> bool:
    """True when a facility row's text marks it as a deposit/summary, not a real
    facility (shared with the import guard in doc_ingest)."""
    from app.services.doc_ingest import _NON_FACILITY_RE

    return bool(_NON_FACILITY_RE.search(text or ""))


_FTYPE_LABEL = {
    "overdraft": "Overdraft", "loan": "Loan", "lc": "Letter of Credit",
    "lg": "Letter of Guarantee", "cheque_discounting": "Cheque Discount",
    "trust_receipt": "Trust Receipt", "lc_sight": "LC Sight",
    "lc_usance": "LC Usance", "log": "Letter of Guarantee",
    "other": "Credit Facility",
}

# ---------------------------------------------------------------------------
# Facility-type catalog — the Offer Letter's "Facility Type" combobox list.
# Built-ins mirror the FacilityType enum (display labels); user-added types are
# stored in SystemSetting("custom_facility_types") as a JSON array so a brand-new
# type typed once becomes selectable everywhere afterwards.
# ---------------------------------------------------------------------------
_BUILTIN_FACILITY_TYPES = [
    "Overdraft", "Loan", "Personal Loan", "Letter of Credit", "Letter of Guarantee",
    "LC Sight", "LC Usance", "Trust Receipt", "Cheque Discounting", "Credit Facility",
]
_FACILITY_TYPES_KEY = "custom_facility_types"


def _norm_ftype(s: str) -> str:
    """Similarity key: case/punctuation/space-insensitive (Latin + Persian/Arabic)."""
    return re.sub(r"[^a-z0-9؀-ۿ]+", "", (s or "").lower())


def _similar_ftype(a: str, b: str) -> bool:
    """Conservative name-similarity: same normalized key, or near-identical text
    (catches 'Personal Loans' vs 'Personal Loan', double spaces, case)."""
    na, nb = _norm_ftype(a), _norm_ftype(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    import difflib

    return difflib.SequenceMatcher(None, na, nb).ratio() >= 0.9


async def _load_custom_ftypes(db: AsyncSession) -> list[str]:
    from app.models.system_setting import SystemSetting

    row = (
        await db.execute(select(SystemSetting).where(SystemSetting.key == _FACILITY_TYPES_KEY))
    ).scalar_one_or_none()
    if row is None or not (row.value or "").strip():
        return []
    try:
        vals = json.loads(row.value)
        return [str(v) for v in vals if str(v).strip()] if isinstance(vals, list) else []
    except Exception:
        return []


def _merged_ftypes(custom: list[str]) -> list[str]:
    out: list[str] = list(_BUILTIN_FACILITY_TYPES)
    for c in custom:
        if not any(_norm_ftype(c) == _norm_ftype(x) for x in out):
            out.append(c)
    return out


@router.get("/facility-types")
async def list_facility_types(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """The Facility Type list for the Offer Letter combobox: built-ins + custom."""
    custom = await _load_custom_ftypes(db)
    return {"ok": True, "types": _merged_ftypes(custom)}


class FacilityTypeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)


@router.post("/facility-types")
async def add_facility_type(
    payload: FacilityTypeCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Add a NEW facility type to the catalog. If a name-similar entry already
    exists (case/punctuation/plural-level match) nothing is added and the
    existing entry is returned — the list stays clean of near-duplicates."""
    from app.models.system_setting import SystemSetting

    name = " ".join((payload.name or "").split())
    if not _norm_ftype(name):
        raise HTTPException(status_code=422, detail="نام نوع تسهیلات معتبر نیست")
    custom = await _load_custom_ftypes(db)
    merged = _merged_ftypes(custom)
    for existing in merged:
        if _similar_ftype(existing, name):
            return {"ok": True, "added": False, "matched": existing, "types": merged}
    custom.append(name)
    row = (
        await db.execute(select(SystemSetting).where(SystemSetting.key == _FACILITY_TYPES_KEY))
    ).scalar_one_or_none()
    if row is None:
        db.add(SystemSetting(key=_FACILITY_TYPES_KEY, value=json.dumps(custom, ensure_ascii=False)))
    else:
        row.value = json.dumps(custom, ensure_ascii=False)
    await db.commit()
    await _audit(db, user, action="create", entity_type="facility_type", account_no="",
                 detail=f"افزودن نوع تسهیلات جدید به فهرست: «{name}»")
    return {"ok": True, "added": True, "matched": name, "types": _merged_ftypes(custom)}


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

    def _ftv(f):
        return str(getattr(f.facility_type, "value", f.facility_type) or "").lower()

    fac = max(facs, key=lambda f: float(f.amount or 0), default=None) if facs else None
    # For a personal loan we want the LOAN facility specifically (not just the
    # biggest), so the loan amount / tenor / installment prefill is correct.
    loan_fac = next((f for f in facs if _ftv(f) == "loan"), None) or fac
    ftype = (getattr(fac.facility_type, "value", fac.facility_type) if fac else "") or ""
    rate = None
    if fac is not None and fac.interest_rate is not None:
        rate = f"{float(fac.interest_rate):g}% p.a."
    loan_rate = None
    if loan_fac is not None and loan_fac.interest_rate is not None:
        loan_rate = f"{float(loan_fac.interest_rate):g}% p.a."

    acct_type = str(getattr(cust.account_type, "value", cust.account_type) or "retail").lower()
    is_corp = acct_type in ("corporate", "sme")
    # Salutation: an explicitly stored one wins; otherwise derive from the type.
    salutation = pget("Salutation", "Title", "Prefix") or ("M/S." if is_corp else "Mr.")

    # Any previously-saved Offer Letter snapshot (ref serial, dates, checkbox
    # state, edited values) so the form restores exactly what was last saved.
    saved = pdata.get("offer_letter") if isinstance(pdata.get("offer_letter"), dict) else {}

    # The customer's recorded guarantors (name + account) so the letter's
    # guarantee items can name them without re-typing. De-duped by name+account.
    guar_rows = (
        await db.execute(
            select(Guarantor).where(
                Guarantor.account_no == acc, Guarantor.is_deleted == False  # noqa: E712
            )
        )
    ).scalars().all()
    seen_guars: set = set()
    guarantors = []
    for g in guar_rows:
        key = ((g.guarantor_name or "").strip().lower(), (g.guarantor_account or "").strip())
        if not key[0] or key in seen_guars:
            continue
        seen_guars.add(key)
        guarantors.append({"name": (g.guarantor_name or "").strip(),
                           "account": (g.guarantor_account or "").strip()})

    return {
        "Guarantors": guarantors,
        "CompanyName": cust.name or "",
        "CompanyNameAr": getattr(cust, "name_ar", "") or "",
        "AccountNumber": acc,
        "AccountType": acct_type,
        "Salutation": salutation,
        "POBox": pget("POBox", "PO Box", "P.O.Box", "POBOX", "Po Box"),
        "CityCountry": pget("CityCountry", "City", "Emirate") or "DUBAI - U.A.E.",
        "Branch": cust.branch or "",
        "Rating": (getattr(prof, "rating", "") or "") if prof else "",
        "BusinessType": ((getattr(prof, "business_type", "") or "") if prof else "") or pget("BusinessType"),
        "FacilityType": _FTYPE_LABEL.get(ftype, "Overdraft"),
        # The latest imported sanction's REQUIRED SECURITIES / DOCUMENTS list
        # (verbatim) — the Offer Letter prefills this over its generic default.
        "RequiredSecurities": pget("RequiredSecurities"),
        "CreditLimit": (f"{float(fac.amount):,.0f}" if fac and fac.amount else ""),
        "InterestRate": rate or "",
        "ExpiryDate": (str(fac.expiry_date) if fac and getattr(fac, "expiry_date", None) else ""),
        "ValidUntil": (str(fac.expiry_date) if fac and getattr(fac, "expiry_date", None) else ""),
        # Loan-specific prefill (for the bilingual Personal Loan template)
        "LoanAmount": (f"{float(loan_fac.amount):,.0f}" if loan_fac and loan_fac.amount else ""),
        "LoanInterestRate": loan_rate or "",
        "LoanTenor": (str(loan_fac.tenor_months) if loan_fac and loan_fac.tenor_months else ""),
        "MonthlyInstallment": (str(loan_fac.installments) if loan_fac and loan_fac.installments else ""),
        "Purpose": (str(loan_fac.purpose) if loan_fac and loan_fac.purpose else ""),
        "facilities_count": len(facs),
        # ALL the account's facilities (largest first) so a multi-facility
        # sanction (مصوبه) imported into the DB lands as multiple table rows on
        # the Offer Letter — row 1 = first entry, the rest become extra rows.
        # Display guard (same regex as the import's v36 fix): a legacy OTHER-typed
        # row whose text says it's really a deposit/summary (the pre-v36 phantom
        # «Credit Facility» rows that may still sit in the DB) is NOT surfaced on
        # the letter. The DB row itself is untouched (review-first) — delete it
        # from the Facilities page when convenient.
        "Facilities": [
            {
                "type": _FTYPE_LABEL.get(_ftv(f2), str(getattr(f2.facility_type, "value", f2.facility_type) or "")),
                "amount": (f"{float(f2.amount):,.0f}" if f2.amount else ""),
                "rate": (f"{float(f2.interest_rate):g}% p.a." if f2.interest_rate is not None else ""),
                "remarks": str(getattr(f2, "notes", "") or getattr(f2, "comments", "") or "")[:300],
                "status": str(getattr(f2.status, "value", f2.status) or ""),
            }
            for f2 in sorted(facs, key=lambda x: float(x.amount or 0), reverse=True)
            if not (_ftv(f2) in ("", "other") and _non_facility_text(
                f"{getattr(f2, 'notes', '') or ''} {getattr(f2, 'comments', '') or ''}"))
        ],
        "Saved": saved,
        # Full parsed profile blob (extracted draft facts live here) so the
        # sanction/مصوبه form can prefill from what was saved earlier.
        "ProfileData": pdata,
    }


class OfferLetterSave(BaseModel):
    """Free-form Offer Letter snapshot to persist on the customer's profile so the
    same values (P.O. Box, salutation, ref, terms, checkbox state) are reusable
    by other forms/reports. Stored in CustomerProfile.data_json."""

    POBox: Optional[str] = None
    CityCountry: Optional[str] = None
    Salutation: Optional[str] = None
    Branch: Optional[str] = None
    snapshot: dict = Field(default_factory=dict)
    snapshot_key: str = "offer_letter"
    fields: dict = Field(default_factory=dict)  # extra top-level scalar facts (deduped by key)


@router.post("/offer-letter-data/{account_no}")
async def save_offer_letter_data(
    account_no: str,
    payload: OfferLetterSave,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Two-way sync: persist the Offer Letter's reusable fields into the customer's
    shared profile record (data_json), creating the profile row if missing. The
    P.O. Box / City / Salutation are lifted to top-level keys so every other form
    reads them; the full snapshot is kept under ``offer_letter``."""
    acc = (account_no or "").strip()
    cust = (
        await db.execute(
            select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False)
        )
    ).scalar_one_or_none()
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    cp = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
    ).scalar_one_or_none()
    if cp is None:
        cp = CustomerProfile(account_no=acc, customer_name=cust.name)
        db.add(cp)

    try:
        data = json.loads(cp.data_json) if cp.data_json else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    # Lift the reusable identity fields to top level (only when non-empty).
    if payload.POBox:
        data["POBox"] = payload.POBox.strip()
    if payload.CityCountry:
        data["CityCountry"] = payload.CityCountry.strip()
    if payload.Salutation:
        data["Salutation"] = payload.Salutation.strip()
    # Arbitrary scalar facts (e.g. from the sanction form) merged top-level →
    # keyed, so re-saving overwrites in place (no duplicates) and other forms
    # can read them.
    for k, v in (payload.fields or {}).items():
        if v not in (None, ""):
            data[str(k)] = v
    # Keep the full snapshot for an exact restore next time, under its own key
    # (offer_letter / sanction / …) so different forms never clobber each other.
    if payload.snapshot:
        data[payload.snapshot_key or "offer_letter"] = payload.snapshot

    cp.data_json = json.dumps(data, ensure_ascii=False)
    # Mirror KYC-relevant facts to their structured columns when provided.
    _f = payload.fields or {}
    if _f.get("trade_license_no"):
        cp.trade_license_no = str(_f["trade_license_no"])[:80]
    if _f.get("trade_license_expiry"):
        cp.trade_license_expiry = str(_f["trade_license_expiry"])[:30]
    if _f.get("business_type") and not (cp.business_type or "").strip():
        cp.business_type = str(_f["business_type"])[:200]
    cp.last_updated = date.today().isoformat()
    cp.updated_by = getattr(user, "username", "") or ""

    # A typed branch can also refresh the customer record (so other views agree).
    if payload.Branch and not cust.branch:
        cust.branch = payload.Branch.strip()[:100]

    await db.commit()
    await _audit(db, user, action="update", entity_type="offer_letter_data", account_no=acc,
                 detail="ذخیرهٔ دادهٔ نامهٔ پیشنهادِ تسهیلات (Offer Letter)")
    return {"ok": True, "account_no": acc, "saved_keys": sorted(data.keys())}


# ---------------------------------------------------------------------------
# Credit-review (مصوبه) first-class persistence — promoted out of data_json so the
# committee-approval facts are searchable / reportable.
# ---------------------------------------------------------------------------
_PROFILE_SCALAR_COLS = [
    "aecb_score", "established_since", "relationship_date", "monthly_salary",
    "auditor", "credit_application_no", "review_date", "proposed_facility",
    "proposed_amount", "proposed_tenor", "proposed_rate", "business_type",
    "trade_license_no", "trade_license_expiry",
]
_REVIEW_SCALAR_COLS = [
    "customer_name", "account_type", "branch", "borrower_type", "request_type",
    "date_of_review", "credit_application_no", "business_activity", "existing_rating",
    "proposed_rating", "rating_notes", "relationship_date", "established_since",
    "ca_expiry_existing", "ca_expiry_proposed", "purpose", "major_changes", "background",
    "pep", "account_conduct", "aecb_score", "cru_findings", "cru_recommendation",
    "monthly_salary", "auditor", "proposed_facility", "proposed_amount", "proposed_tenor",
    "proposed_rate",
]
_SN2REVIEW = {
    "CustomerName": "customer_name", "BranchName": "branch", "BorrowerType": "borrower_type",
    "RequestType": "request_type", "DateOfReview": "date_of_review", "CreditAppNo": "credit_application_no",
    "BusinessActivity": "business_activity", "ExistingRating": "existing_rating",
    "ProposedRating": "proposed_rating", "RatingNotes": "rating_notes", "RelationshipDate": "relationship_date",
    "EstablishedSince": "established_since", "CAExpiryExisting": "ca_expiry_existing",
    "CAExpiryProposed": "ca_expiry_proposed", "Purpose": "purpose", "MajorChanges": "major_changes",
    "Background": "background", "PEP": "pep", "AccountConduct": "account_conduct", "AECBScore": "aecb_score",
    "CRUFindings": "cru_findings", "CRURecommendation": "cru_recommendation", "MonthlySalary": "monthly_salary",
    "AuditorName": "auditor",
}


def _set_col(obj, name: str, value):
    if value in (None, ""):
        return
    col = obj.__table__.columns.get(name)
    ml = getattr(getattr(col, "type", None), "length", None)
    setattr(obj, name, str(value)[:ml] if ml else str(value))


def _apply_profile_scalars(cp, d: dict):
    """Write the promoted first-class facts onto the profile."""
    for k in _PROFILE_SCALAR_COLS:
        if k == "business_type" and (cp.business_type or "").strip():
            continue  # never clobber an existing business type
        _set_col(cp, k, d.get(k))


async def _upsert_credit_review(db, account_no: str, rf: dict, source: str, username: str):
    """Upsert ONE row per (account, review date): re-saving the same review updates
    in place (no duplicates); a new review date adds a history row."""
    review_date = str(rf.get("date_of_review") or "").strip()
    q = select(CreditReview).where(
        CreditReview.account_no == account_no,
        CreditReview.is_deleted == False,  # noqa: E712
    )
    if review_date:
        q = q.where(CreditReview.date_of_review == review_date)
    else:
        q = q.where((CreditReview.date_of_review == None) | (CreditReview.date_of_review == ""))  # noqa: E711
    row = (await db.execute(q.order_by(CreditReview.created_at.desc()).limit(1))).scalar_one_or_none()
    created = row is None
    if row is None:
        row = CreditReview(account_no=account_no, created_by=username)
        db.add(row)
    for c in _REVIEW_SCALAR_COLS:
        _set_col(row, c, rf.get(c))
    for jc, key in [("limits_json", "limits"), ("recip_json", "recip"), ("fin_json", "fin"),
                    ("guarantors_json", "guars"), ("banks_json", "banks")]:
        if rf.get(key) is not None:
            setattr(row, jc, json.dumps(rf.get(key), ensure_ascii=False))
    row.source = source
    return row, created


def _review_out(r: CreditReview) -> dict:
    return {
        "id": r.id, "account_no": r.account_no, "customer_name": r.customer_name,
        "account_type": r.account_type, "date_of_review": r.date_of_review,
        "proposed_facility": r.proposed_facility, "proposed_amount": r.proposed_amount,
        "proposed_tenor": r.proposed_tenor, "proposed_rate": r.proposed_rate,
        "aecb_score": r.aecb_score, "proposed_rating": r.proposed_rating, "purpose": r.purpose,
        "cru_recommendation": r.cru_recommendation, "source": r.source,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


class SanctionSave(BaseModel):
    snapshot: dict = Field(default_factory=dict)
    limits: list = Field(default_factory=list)
    recip: list = Field(default_factory=list)
    fin: list = Field(default_factory=list)
    guars: list = Field(default_factory=list)
    banks: list = Field(default_factory=list)


@router.post("/sanction/{account_no}")
async def save_sanction(
    account_no: str,
    payload: SanctionSave,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Persist the credit-committee approval (مصوبه) form: a first-class
    ``credit_reviews`` row (deduped per review date) + the promoted profile
    columns + the exact snapshot under data_json["sanction"] for restore."""
    from app.services.customer_link import ensure_customer

    acc = (account_no or "").strip()
    cust = await ensure_customer(db, acc, (payload.snapshot or {}).get("CustomerName"))
    sn = payload.snapshot or {}
    username = getattr(user, "username", "") or ""

    # Review row fields from the form snapshot.
    rf = {col: sn.get(k) for k, col in _SN2REVIEW.items()}
    bt = str(sn.get("BorrowerType", "")).lower()
    rf["account_type"] = "corporate" if ("corp" in bt or "sme" in bt) else "retail"
    rf.update(limits=payload.limits, recip=payload.recip, fin=payload.fin,
              guars=payload.guars, banks=payload.banks)
    review, created = await _upsert_credit_review(db, acc, rf, "sanction_form", username)
    if cust is not None and not review.customer_name:
        review.customer_name = cust.name

    # Profile: promote the reusable scalars + keep the exact snapshot for restore.
    cp = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
    ).scalar_one_or_none()
    if cp is None:
        cp = CustomerProfile(account_no=acc, customer_name=cust.name if cust else None)
        db.add(cp)
    _apply_profile_scalars(cp, {
        "aecb_score": sn.get("AECBScore"), "established_since": sn.get("EstablishedSince"),
        "relationship_date": sn.get("RelationshipDate"), "monthly_salary": sn.get("MonthlySalary"),
        "auditor": sn.get("AuditorName"), "credit_application_no": sn.get("CreditAppNo"),
        "review_date": sn.get("DateOfReview"), "business_type": sn.get("BusinessActivity"),
    })
    try:
        data = json.loads(cp.data_json) if cp.data_json else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    data["sanction"] = {**sn, "limits": payload.limits, "recip": payload.recip,
                        "fin": payload.fin, "guars": payload.guars, "banks": payload.banks}
    cp.data_json = json.dumps(data, ensure_ascii=False)
    cp.last_updated = date.today().isoformat()
    cp.updated_by = username
    if sn.get("BranchName") and cust is not None and not (cust.branch or "").strip():
        cust.branch = str(sn["BranchName"])[:100]

    await db.commit()
    await _audit(db, user, action="create" if created else "update", entity_type="sanction",
                 account_no=acc, entity_id=review.id,
                 detail=f"{'ثبتِ' if created else 'به‌روزرسانیِ'} مصوبهٔ کمیتهٔ اعتباری"
                        + (f" — تاریخِ بررسی {review.date_of_review}" if review.date_of_review else ""))
    return {"ok": True, "account_no": acc, "review_id": review.id, "created": created}


@router.get("/credit-reviews/{account_no}")
async def list_credit_reviews(
    account_no: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """All credit-committee reviews for an account (newest first) — the queryable
    history that feeds reports/dashboards."""
    rows = (
        await db.execute(
            select(CreditReview)
            .where(CreditReview.account_no == (account_no or "").strip(),
                   CreditReview.is_deleted == False)  # noqa: E712
            .order_by(CreditReview.created_at.desc())
        )
    ).scalars().all()
    return [_review_out(r) for r in rows]


@router.post("/extract-draft")
async def extract_draft(
    file: UploadFile = File(...),
    account_no: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Parse a filled credit-committee approval DRAFT (.docx) and (a) return the
    fields that prefill the Offer Letter, and (b) persist everything extracted to
    the customer's record — idempotently, so re-extracting or later printing the
    Offer Letter never creates duplicates:
      • scalar facts (trade license, AECB score, address, proposed terms, …) are
        keyed entries in the profile data_json / KYC columns → overwrite in place;
      • guarantors are upserted by (account, guarantor account / name).
    """
    from app.services.customer_link import ensure_customer
    from app.models.customer import AccountType

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    if not (file.filename or "").lower().endswith((".docx",)):
        raise HTTPException(status_code=415, detail="Please upload a Word .docx draft")
    try:
        from app.services.draft_extract import extract_from_docx  # needs python-docx
    except Exception as exc:  # pragma: no cover - dependency guard
        raise HTTPException(status_code=503, detail=f"Draft parser unavailable on server ({exc}). Install python-docx.")
    try:
        parsed = extract_from_docx(raw)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=422, detail=f"Could not read the draft: {exc}")

    acc = (account_no or "").strip() or (parsed.get("account_no") or "").strip()
    if not acc:
        raise HTTPException(status_code=422, detail="No account number found in the draft.")

    offer = parsed.get("offer", {})
    pf = parsed.get("profile", {})

    customer = await ensure_customer(db, acc, offer.get("CompanyName"))
    if customer is not None:
        at = offer.get("AccountType")
        if at in ("retail", "corporate", "sme"):
            customer.account_type = AccountType(at)
        if pf.get("address") and not (customer.address or "").strip():
            customer.address = pf["address"]
        if parsed.get("branch_code") and not (customer.branch or "").strip():
            customer.branch = parsed["branch_code"][:100]

    cp = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
    ).scalar_one_or_none()
    if cp is None:
        cp = CustomerProfile(account_no=acc, customer_name=offer.get("CompanyName"))
        db.add(cp)
    try:
        data = json.loads(cp.data_json) if cp.data_json else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    # Merge extracted scalar facts (keyed → no duplicates on re-extract).
    for k, v in pf.items():
        if v:
            data[k] = v
    data["draft_extracted_at"] = datetime.now().isoformat(timespec="seconds")
    cp.data_json = json.dumps(data, ensure_ascii=False)
    # Promote the extracted facts to their first-class profile columns.
    _apply_profile_scalars(cp, pf)
    cp.last_updated = date.today().isoformat()
    cp.updated_by = getattr(user, "username", "") or ""

    # Guarantors — upsert (dedupe), never scatter duplicates.
    g_added = g_updated = 0
    for g in parsed.get("guarantors", []):
        gname = (g.get("name") or "").strip()
        gacc = (g.get("account") or "").strip()
        if not gname:
            continue
        if gacc:
            await ensure_customer(db, gacc, gname)
        row = None
        if gacc:
            row = (
                await db.execute(
                    select(Guarantor).where(
                        Guarantor.account_no == acc,
                        Guarantor.guarantor_account == gacc,
                        Guarantor.is_deleted == False,  # noqa: E712
                    )
                )
            ).scalar_one_or_none()
        if row is None:
            row = (
                await db.execute(
                    select(Guarantor).where(
                        Guarantor.account_no == acc,
                        Guarantor.guarantor_name == gname,
                        Guarantor.is_deleted == False,  # noqa: E712
                    )
                )
            ).scalar_one_or_none()
        if row is None:
            gid = f"G-{acc}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:2]}"
            row = Guarantor(id=gid, account_no=acc, date_added=date.today().isoformat(),
                            created_by=getattr(user, "username", "") or "")
            db.add(row)
            g_added += 1
        else:
            g_updated += 1
        row.guarantor_name = gname[:200]
        if gacc:
            row.guarantor_account = gacc[:50]
        if g.get("branch"):
            row.branch = g["branch"][:20]
        if customer is not None and getattr(customer, "name", None) and not row.customer_name:
            row.customer_name = customer.name

    # Record the extracted draft as a first-class credit-review (deduped per date).
    rf = {
        "customer_name": offer.get("CompanyName"), "account_type": offer.get("AccountType"),
        "branch": offer.get("Branch"), "borrower_type": offer.get("AccountType"),
        "date_of_review": pf.get("review_date"), "credit_application_no": pf.get("credit_application_no"),
        "business_activity": offer.get("BusinessType"), "proposed_rating": offer.get("Rating"),
        "rating_notes": (f"Proposed interest rate {pf.get('proposed_rate')}" if pf.get("proposed_rate") else None),
        "relationship_date": pf.get("relationship_date"), "established_since": pf.get("established_since"),
        "purpose": offer.get("Purpose"), "aecb_score": pf.get("aecb_score"),
        "background": pf.get("customer_profile"), "monthly_salary": pf.get("monthly_salary"),
        "auditor": pf.get("auditor"), "proposed_facility": pf.get("proposed_facility") or offer.get("FacilityType"),
        "proposed_amount": pf.get("proposed_amount"), "proposed_tenor": pf.get("proposed_tenor"),
        "proposed_rate": pf.get("proposed_rate"),
    }
    review, _rcreated = await _upsert_credit_review(db, acc, rf, "draft_extract", getattr(user, "username", "") or "")

    try:
        await recompute_completeness(db, acc)
    except Exception:
        pass
    await db.commit()
    return {
        "ok": True,
        "account_no": acc,
        "review_id": review.id,
        "account_type": offer.get("AccountType", ""),
        "offer": offer,
        "profile": pf,
        "guarantors": parsed.get("guarantors", []),
        "profile_keys": sorted([k for k in pf.keys() if pf[k]]),
        "guarantors_added": g_added,
        "guarantors_updated": g_updated,
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
    await _audit(db, user, action="create", entity_type="note", account_no=account_no, entity_id=nid,
                 detail=f"یادداشت: {(n.title or n.content or '')[:80]}")
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
    """Create a per-customer child row, guaranteeing it is linked to a customer.

    This is the single choke point for adding any account_no-keyed child
    (properties, fixed deposits, partners, …): it ensures the owning customer
    exists (auto-creating a stub profile for an orphan account_no) and stamps the
    denormalised ``customer_name`` when the model has one — so every child record,
    including future ones added through this helper, is reachable from a profile
    rather than stranded in its own list.
    """
    from app.services.customer_link import ensure_customer

    customer = await ensure_customer(db, account_no, data.get("customer_name"))
    obj = model(
        id=_new_child_id(prefix, account_no),
        account_no=account_no,
        date_added=date.today().isoformat(),
        created_by=getattr(user, "username", "") or "",
    )
    if "customer_name" in model.__table__.columns and not data.get("customer_name") and customer is not None:
        obj.customer_name = (customer.name or "")[:200]
    _apply_child_fields(obj, data, allowed)
    ent = {MortgagedProperty: ("property", "ملکِ مرهونه"),
           FixedDeposit: ("fixed_deposit", "سپردهٔ ثابت"),
           Partner: ("partner", "شریک")}.get(model)

    # Entry guard (SAME rules as the cleanup engine), tiered so it never loses data
    # nor wrongly merges distinct records:
    #   • CERTAIN duplicate (same strong id, identical key values) → enrich the
    #     existing record in place; no duplicate is created.
    #   • PROBABLE (same strong id but a key value differs — an update OR a distinct
    #     sub-entity like another unit) → insert it, but FLAG it for review so the
    #     scan + AI adjudicator can decide. Applies to import, manual add & AI adds.
    from app.services import db_cleanup

    probable_of = None
    if db_cleanup.matcher_for(model) is not None:
        existing_rows = list((await db.execute(
            select(model).where(model.account_no == account_no,
                                model.is_deleted == False))).scalars().all())  # noqa: E712
        dup = db_cleanup.find_duplicate(obj, existing_rows, model=model)
        if dup is not None:
            if db_cleanup.dup_status(dup, obj, model=model) == "certain":
                filled = db_cleanup.merge_fill(dup, obj, model=model)
                await db.commit()
                if ent:
                    extra = f" (فیلدها: {'، '.join(filled)})" if filled else ""
                    await _audit(db, user, action="update", entity_type=ent[0], account_no=account_no,
                                 entity_id=dup.id,
                                 detail=f"گاردِ دیتابیس: به‌جای ایجادِ {ent[1]}ِ تکراری، رکوردِ موجود تکمیل شد{extra}")
                result = _child_dict(dup)
                result["deduped"] = True
                return result
            probable_of = dup.id   # same id, differing value → insert + flag below

    db.add(obj)
    await db.commit()
    if ent:
        await _audit(db, user, action="create", entity_type=ent[0], account_no=account_no,
                     entity_id=obj.id, detail=f"افزودنِ {ent[1]}")
        if probable_of:
            await _audit(db, user, action="review", entity_type=ent[0], account_no=account_no,
                         entity_id=obj.id,
                         detail=f"احتمالِ تکرار/به‌روزرسانیِ {ent[1]} با رکوردِ {probable_of} "
                                "(همان شناسه، مقادیرِ متفاوت) — برای داوری به «پاک‌سازیِ دیتابیس» مراجعه شود")
    result = _child_dict(obj)
    if probable_of:
        result["needs_review"] = True
    return result


async def _update_child(db, model, item_id, data, allowed):
    obj = (await db.execute(select(model).where(model.id == item_id))).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found")
    _apply_child_fields(obj, data, allowed)
    await db.commit()
    return _child_dict(obj)


async def _delete_child(db, model, item_id, user=None, entity_type=None, label=None):
    obj = (await db.execute(select(model).where(model.id == item_id))).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found")
    obj.is_deleted = True
    acc = getattr(obj, "account_no", None)
    await db.commit()
    if entity_type:
        await _audit(db, user, action="delete", entity_type=entity_type, account_no=acc,
                     entity_id=item_id, detail=f"حذفِ {label or entity_type}")
    return {"ok": True, "id": item_id, "deleted": True}


# ---- Mortgaged properties (A12) ----
_PROPERTY_FIELDS = {
    "facility_id", "customer_name", "country", "plate_no", "mortgage_deed_no",
    "city", "address", "prop_type", "building_age", "land_area", "cnbc",
    "zone", "infra_area", "owner", "owner_national_id", "postal_code",
    "valuation", "valuation_currency", "insurance_expiry", "insurance_issue",
    "insurance_no", "insurance_computer_code",
    "last_valuation_date", "mortgage_date", "mortgage_amount", "mortgage_currency", "remarks",
}


class PropertyCreate(BaseModel):
    facility_id: str = ""
    country: str = ""
    plate_no: str = ""
    mortgage_deed_no: str = ""
    city: str = ""
    address: str = ""
    prop_type: str = ""
    building_age: str = ""
    land_area: str = ""
    cnbc: str = ""
    zone: str = ""
    infra_area: str = ""
    owner: str = ""
    owner_national_id: str = ""
    postal_code: str = ""
    valuation: Optional[float] = None
    valuation_currency: str = "AED"
    insurance_expiry: str = ""
    insurance_issue: str = ""
    insurance_no: str = ""
    insurance_computer_code: str = ""
    last_valuation_date: str = ""
    mortgage_date: str = ""
    mortgage_amount: Optional[float] = None
    mortgage_currency: str = "AED"
    remarks: str = ""


class PropertyUpdate(BaseModel):
    facility_id: Optional[str] = None
    country: Optional[str] = None
    plate_no: Optional[str] = None
    mortgage_deed_no: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    prop_type: Optional[str] = None
    building_age: Optional[str] = None
    land_area: Optional[str] = None
    cnbc: Optional[str] = None
    zone: Optional[str] = None
    infra_area: Optional[str] = None
    owner: Optional[str] = None
    owner_national_id: Optional[str] = None
    postal_code: Optional[str] = None
    valuation: Optional[float] = None
    valuation_currency: Optional[str] = None
    insurance_expiry: Optional[str] = None
    insurance_issue: Optional[str] = None
    insurance_no: Optional[str] = None
    insurance_computer_code: Optional[str] = None
    last_valuation_date: Optional[str] = None
    mortgage_date: Optional[str] = None
    mortgage_amount: Optional[float] = None
    mortgage_currency: Optional[str] = None
    remarks: Optional[str] = None


@router.post("/properties/{account_no}")
async def add_property(
    account_no: str, payload: PropertyCreate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Add a mortgaged property to a customer's profile.

    Linking (and stub-customer creation for an orphan account_no) is handled
    centrally by ``_add_child``.
    """
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
    return await _delete_child(db, MortgagedProperty, item_id, user, "property", "ملکِ مرهونه")


class PropertyEventCreate(BaseModel):
    # valuation | mortgage | remortgage | additional_mortgage | release | insurance | other
    event_type: str = Field(min_length=3, max_length=30)
    event_date: str = ""
    amount: Optional[float] = None
    currency: str = ""
    remarks: str = ""


@router.post("/properties/{property_id}/events")
async def add_property_event(
    property_id: str, payload: PropertyEventCreate,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    """Add one dated event to a property's timeline (several valuations,
    mortgage / re-mortgage / release / insurance…) — manual counterpart of the
    import's event history."""
    import uuid as _uuid
    from datetime import datetime as _dt

    prop = (await db.execute(select(MortgagedProperty).where(
        MortgagedProperty.id == property_id))).scalar_one_or_none()
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    et = payload.event_type.strip().lower().replace("-", "_").replace(" ", "_")
    if et not in {"valuation", "mortgage", "remortgage", "additional_mortgage",
                  "release", "insurance", "other"}:
        raise HTTPException(status_code=422, detail="نوعِ رویداد نامعتبر است")
    if not payload.event_date.strip() and payload.amount is None:
        raise HTTPException(status_code=422, detail="رویداد باید دست‌کم تاریخ یا مبلغ داشته باشد")
    ev = PropertyEvent(
        id=f"PE-{_dt.now().strftime('%Y%m%d%H%M%S')}-{_uuid.uuid4().hex[:8]}",
        property_id=property_id, account_no=prop.account_no, event_type=et,
        event_date=payload.event_date.strip()[:30], amount=payload.amount,
        currency=payload.currency.strip()[:10], remarks=payload.remarks.strip()[:400],
        source="manual", created_by=getattr(user, "username", "") or "",
    )
    db.add(ev)
    await db.commit()
    await _audit(db, user, action="create", entity_type="property_event",
                 account_no=prop.account_no, entity_id=ev.id,
                 detail=f"رویدادِ ملک «{et}» ({ev.event_date or '—'}) برای {prop.plate_no or prop.mortgage_deed_no or property_id}")
    return _child_dict(ev)


@router.delete("/property-events/{event_id}")
async def delete_property_event(
    event_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    ev = (await db.execute(select(PropertyEvent).where(PropertyEvent.id == event_id))).scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")
    ev.is_deleted = True
    await db.commit()
    await _audit(db, user, action="delete", entity_type="property_event",
                 account_no=ev.account_no, entity_id=ev.id,
                 detail=f"حذفِ رویدادِ ملک «{ev.event_type}» ({ev.event_date or '—'})")
    return {"ok": True}


# ---- Fixed deposits (A12) ----
_FD_FIELDS = {"facility_id", "customer_name", "fd_number", "amount", "currency",
              "open_date", "maturity_date", "rate", "remarks"}


class FixedDepositCreate(BaseModel):
    facility_id: str = ""
    fd_number: str = ""
    amount: Optional[float] = None
    currency: str = "AED"
    open_date: str = ""
    maturity_date: str = ""
    rate: str = ""
    remarks: str = ""


class FixedDepositUpdate(BaseModel):
    facility_id: Optional[str] = None
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
    return await _delete_child(db, FixedDeposit, item_id, user, "fixed_deposit", "سپردهٔ ثابت")


# ---- Partners / shareholders ----
_PARTNER_FIELDS = {"facility_id", "customer_name", "name", "role", "nationality", "national_id",
                   "passport_no", "passport_issue", "passport_expiry",
                   "emirates_id_no", "emirates_id_expiry", "share", "remarks"}


class PartnerCreate(BaseModel):
    facility_id: str = ""
    name: str = Field(..., min_length=1, max_length=200)
    role: str = ""
    nationality: str = ""
    national_id: str = ""
    passport_no: str = ""
    passport_issue: str = ""
    passport_expiry: str = ""
    emirates_id_no: str = ""
    emirates_id_expiry: str = ""
    share: str = ""
    remarks: str = ""


class PartnerUpdate(BaseModel):
    facility_id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    nationality: Optional[str] = None
    national_id: Optional[str] = None
    passport_no: Optional[str] = None
    passport_issue: Optional[str] = None
    passport_expiry: Optional[str] = None
    emirates_id_no: Optional[str] = None
    emirates_id_expiry: Optional[str] = None
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
    return await _delete_child(db, Partner, item_id, user, "partner", "شریک")


@router.get("/partner-names")
async def partner_names(db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    """Distinct partner/shareholder names for autocomplete (search & select)."""
    rows = (
        await db.execute(
            select(Partner.name).where(
                Partner.name.isnot(None), Partner.name != "",
                Partner.is_deleted == False,  # noqa: E712
            ).distinct().limit(1000)
        )
    ).scalars().all()
    return sorted({(n or "").strip() for n in rows if (n or "").strip()})


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
        # Where the bytes actually live, so the UI can show it and ops can audit it.
        "storage": "drive" if (a.drive_file_id or "") else "disk",
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
    """Upload a document and record its metadata (scoped to a facility + checklist
    row, or shared).

    Storage strategy — keep large binaries OUT of the database/ephemeral disk:
      * When Google Drive sync is enabled, the file is stored IN Drive (filed
        under attachments/cust-<acc>/fac-<fac> with a traceable name) and only the
        Drive file id is kept in the DB — nothing is written to local disk.
      * When Drive is disabled, OR the Drive upload fails, it falls back to the
        on-disk store so an upload is never lost.
    """
    data = await file.read()
    original_name = file.filename or "file"
    mimetype = file.content_type or "application/octet-stream"

    drive_file_id = ""
    stored = ""
    rel = ""
    size = len(data)

    from app.services import drive_sync

    if drive_sync.is_enabled():
        try:
            res = await drive_sync.sync_attachment(
                account_no=account_no,
                facility_id=facility_id or "",
                original_name=original_name,
                data=data,
                mimetype=mimetype,
            )
            if res.get("ok"):
                drive_file_id = res["result"]["id"]
                stored = res["result"]["name"]  # traceable Drive name
        except Exception:  # noqa: BLE001 - fall back to disk on any Drive error
            drive_file_id = ""

    if not drive_file_id:
        # Drive disabled or upload failed -> persist on disk so nothing is lost.
        rel, size, stored = await attachments_store.save_bytes(
            account_no, facility_id, original_name, data
        )

    aid = f"A-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}"
    a = Attachment(
        id=aid, account_no=account_no, facility_id=(facility_id or "")[:60],
        row_index=(row_index or "")[:10], file_name=stored[:255],
        original_name=original_name[:255], file_path=rel,
        drive_file_id=drive_file_id or None,
        file_size=str(size), upload_date=date.today().isoformat(),
        uploaded_by=getattr(user, "username", "") or "",
        is_shared="1" if is_shared else "0", notes=notes or "",
    )
    db.add(a)
    await db.commit()
    await _audit(db, user, action="upload", entity_type="attachment", account_no=account_no, entity_id=aid,
                 detail=f"بارگذاری مدرک: {original_name}")
    return _attachment_dict(a)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Stream a stored document back so it actually opens again (fixes A15).

    Serves from Google Drive when the file lives there, otherwise from disk.
    """
    import mimetypes

    a = (await db.execute(select(Attachment).where(Attachment.id == attachment_id))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    download_name = a.original_name or a.file_name or "document"

    # Drive-stored file: pull the bytes from Drive and stream them back.
    if a.drive_file_id:
        from app.services import drive_sync, google_drive

        try:
            data = await drive_sync.download_attachment(a.drive_file_id)
        except google_drive.DriveError as exc:
            raise HTTPException(status_code=502, detail=f"Drive download failed: {exc}")
        mime = mimetypes.guess_type(download_name)[0] or "application/octet-stream"
        return Response(
            content=data, media_type=mime,
            headers={"Content-Disposition": _content_disposition("attachment", download_name)},
        )

    # Legacy / disk-stored file.
    path = attachments_store.resolve(a.file_path or "")
    if path is None:
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(str(path), filename=download_name)


@router.get("/attachments/{attachment_id}/view")
async def view_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Stream a document INLINE (Content-Disposition: inline) so the browser opens
    it in a viewer (and honors #page=N) instead of downloading it."""
    import mimetypes

    a = (await db.execute(select(Attachment).where(Attachment.id == attachment_id))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    name = a.original_name or a.file_name or "document"
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    if a.drive_file_id:
        from app.services import drive_sync, google_drive
        try:
            data = await drive_sync.download_attachment(a.drive_file_id)
        except google_drive.DriveError as exc:
            raise HTTPException(status_code=502, detail=f"Drive download failed: {exc}")
        return Response(content=data, media_type=mime,
                        headers={"Content-Disposition": _content_disposition("inline", name)})
    path = attachments_store.resolve(a.file_path or "")
    if path is None:
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(str(path), filename=name, content_disposition_type="inline")


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Remove an attachment record and its stored file (from Drive and/or disk)."""
    a = (await db.execute(select(Attachment).where(Attachment.id == attachment_id))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete the bytes wherever they live. Both are best-effort: a failed remote
    # delete must not block removing the DB record (it would leave an orphan row).
    if a.drive_file_id:
        try:
            from app.services import drive_sync

            await drive_sync.delete_attachment(a.drive_file_id)
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass
    path = attachments_store.resolve(a.file_path or "")
    if path is not None:
        try:
            path.unlink()
        except OSError:
            pass

    acc = a.account_no
    name = a.original_name or a.file_name or attachment_id
    await db.delete(a)
    await db.commit()
    await _audit(db, user, action="delete", entity_type="attachment", account_no=acc,
                 entity_id=attachment_id, detail=f"حذفِ مدرک: {name}")
    return {"ok": True, "id": attachment_id, "deleted": True}


# ===========================================================================
# Credit-file Summary — server-generated PDF (the Excel GenerateSummaryReport).
# Draws from the structured data (profile, facilities, guarantors, securities,
# properties, FDs, partners) so it is the single source, and is downloadable
# instead of browser-print-only.
# ===========================================================================
@router.get("/summary/{account_no}/export.pdf")
async def export_summary_pdf(
    account_no: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Generate a credit-file summary PDF (Corporate/Retail) for one customer."""
    from app.services.exporters import build_pdf
    from app.models.security import Security

    acc = (account_no or "").strip()
    cust = (
        await db.execute(select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False))
    ).scalar_one_or_none()
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    prof = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
    ).scalar_one_or_none()
    facs = (
        await db.execute(select(Facility).where(Facility.customer_id == cust.id, Facility.is_deleted == False))
    ).scalars().all()

    async def _by_acc(model, order=None):
        q = select(model).where(model.account_no == acc)
        if hasattr(model, "is_deleted"):
            q = q.where(model.is_deleted == False)  # noqa: E712
        if order is not None:
            q = q.order_by(order)
        return (await db.execute(q)).scalars().all()

    guars = await _by_acc(Guarantor)
    secs = await _by_acc(Security, order=Security.year.desc())
    props = await _by_acc(MortgagedProperty)
    fds = await _by_acc(FixedDeposit)
    partners = await _by_acc(Partner)

    def _money(v, cur="AED"):
        try:
            return f"{cur} {float(v or 0):,.0f}"
        except (TypeError, ValueError):
            return str(v or "")

    def _ev(x):
        return getattr(x, "value", x)

    sections: list = [(
        "Facilities", ["Ref / Name", "Type", "Amount", "Status", "Expiry"],
        [[f.name or f.id, _ev(f.facility_type), _money(f.amount, f.currency or "AED"), _ev(f.status),
          str(f.expiry_date or f.end_date or "") or "—"] for f in facs],
    )]
    if prof is not None:
        kyc = [
            ("Trade Licence", prof.trade_license_no, prof.trade_license_issue, prof.trade_license_expiry, prof.trade_license_remarks),
            ("Passport", prof.passport_no, prof.passport_issue, prof.passport_expiry, prof.passport_remarks),
            ("Emirates ID", prof.emirates_id_no, prof.emirates_id_issue, prof.emirates_id_expiry, prof.emirates_id_remarks),
            ("Visa", prof.visa_no, prof.visa_issue, prof.visa_expiry, prof.visa_type),
            ("Tenancy", prof.tenancy_no, prof.tenancy_issue, prof.tenancy_expiry, prof.tenancy_address),
        ]
        sections.append((
            "KYC Documents", ["Document", "Number", "Issue", "Expiry", "Remarks / Sub-field"],
            [[d[0], d[1] or "—", d[2] or "—", d[3] or "—", d[4] or "—"] for d in kyc],
        ))
    if guars:
        sections.append((
            "Guarantors & Security Cheques", ["Name", "Account", "Cheque No", "Amount", "Bank"],
            [[g.guarantor_name, g.guarantor_account, g.cheque_no, _money(g.cheque_amount), g.issuing_bank] for g in guars],
        ))
    if props:
        sections.append((
            "Mortgaged Properties", ["Plate", "Deed No", "City", "Type", "Valuation", "Mortgage Amt", "Ins. Expiry"],
            [[p.plate_no, p.mortgage_deed_no, p.city, p.prop_type, _money(p.valuation, p.valuation_currency or "AED"),
              _money(p.mortgage_amount), p.insurance_expiry] for p in props],
        ))
    if fds:
        sections.append((
            "Fixed Deposits", ["Number", "Amount", "Currency", "Open", "Maturity", "Rate"],
            [[d.fd_number, _money(d.amount, d.currency or "AED"), d.currency, d.open_date, d.maturity_date, d.rate] for d in fds],
        ))
    if partners:
        sections.append((
            "Partners / Shareholders", ["Name", "Nationality", "Share %"],
            [[p.name, p.nationality, p.share] for p in partners],
        ))
    if secs:
        sections.append((
            f"Securities Register ({len(secs)})", ["Year", "Cheque No", "Amount", "Bank", "Remarks"],
            [[s.year, s.cheque_no, _money(s.cheque_amount_num), s.issuing_bank, s.remarks] for s in secs[:40]],
        ))

    exposure = sum(float(f.amount or 0) for f in facs)
    meta = {
        "Account": acc, "Branch": cust.branch or "—", "Type": _ev(cust.account_type),
        "Rating": (getattr(prof, "rating", "") if prof else "") or "—",
        "Total exposure": _money(exposure),
        "Completeness": (getattr(prof, "profile_completeness", "") if prof else "") or "—",
    }
    content, media = build_pdf(f"Credit File Summary — {cust.name or acc}", sections, meta)
    ext = "pdf" if media == "application/pdf" else "html"
    return Response(
        content=content, media_type=media,
        headers={"Content-Disposition": f'attachment; filename="credit-summary-{acc}.{ext}"'},
    )


# ===========================================================================
# Daily log — smart routing (A22). Free text in; 6-digit account numbers are
# extracted (a number immediately followed by a currency word is treated as an
# amount, not an account), matched against known customers, and routed to each
# as a follow-up task. A journal entry is always recorded; unknown numbers come
# back for the user to confirm/create.
# ===========================================================================
_CURRENCY_WORDS = {
    "ریال", "ریالی", "درهم", "دلار", "تومان", "irr", "rial", "rials",
    "dirham", "dirhams", "aed", "usd", "eur", "$",
}


def _extract_accounts(text: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(r"(?<!\d)(\d{6})(?!\d)", text or ""):
        tail = (text[m.end():m.end() + 18]).strip().lower()
        nxt = re.split(r"[\s,.:;()/\-]+", tail, maxsplit=1)[0] if tail else ""
        if nxt in _CURRENCY_WORDS:
            continue  # it's an amount, not an account number
        out.append(m.group(1))
    seen, uniq = set(), []
    for a in out:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


class DailyLog(BaseModel):
    text: str = Field(..., min_length=1)
    followup_date: str = ""


@router.post("/daily-log")
async def daily_log(
    payload: DailyLog,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Record a daily-log line and route it to any customer account mentioned."""
    text = payload.text.strip()
    accounts = _extract_accounts(text)
    uname = getattr(user, "username", "") or ""
    today = date.today().isoformat()

    jid = "J-" + uuid.uuid4().hex[:18]
    db.add(JournalEntry(
        id=jid, account_no=(accounts[0] if accounts else ""), item=text[:100],
        action="Daily log", source="Daily Log", date=today, user=uname, notes=text[:1000],
    ))

    matched: list[dict] = []
    unknown: list[str] = []
    for acc in accounts:
        cust = (
            await db.execute(select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False))  # noqa: E712
        ).scalar_one_or_none()
        if cust is None:
            unknown.append(acc)
            continue
        tid = f"T-{acc}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}"
        db.add(CustomTask(
            id=tid, account_no=acc, facility_id="", task_name=text[:200], status="",
            followup_date=(payload.followup_date or "")[:30], notes="Routed from daily log",
            priority="Medium", created_by=uname, created_date=today, completed_date="", is_active="1",
        ))
        matched.append({"account_no": acc, "customer_name": cust.name, "task_id": tid})
        # v86 — the customer page's «لاگِ کارها» tab reads the ACTIVITY log; a
        # daily-log line routed to this account must show up there too (owner:
        # «ذیل لاگ اون حساب دیدم چیزی ثبت نشده»). Journal + task alone are
        # invisible to that tab.
        await _audit(db, user, action="create", entity_type="daily_log",
                     account_no=acc, entity_id=jid,
                     detail=f"لاگ روزانه: {text[:300]}"
                            + (f" — پیگیری: {payload.followup_date}" if payload.followup_date else ""))
    await db.commit()
    return {"journal_id": jid, "accounts_found": accounts, "routed": matched, "unknown_accounts": unknown}


# ===========================================================================
# Backup — download the whole CRM dataset as JSON (A21, web equivalent). A true
# incremental, offline-resync backup of file shares is a desktop concern; for the
# cloud DB the appropriate backup is a portable export an admin can download/keep.
# ===========================================================================
@router.get("/backup/export.json")
async def backup_export(db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """Export all CRM business data (excludes users/personal notes) as JSON.

    Streamed to a temp file one page at a time (then sent + deleted) so a large DB
    never builds a full JSON blob in RAM and OOMs the instance."""
    import os
    import tempfile
    from starlette.background import BackgroundTask
    from app.services.backup import stream_backup_to_file

    def _rm(p):
        try: os.remove(p)
        except OSError: pass

    fd, tmp = tempfile.mkstemp(suffix=".json", prefix="allin1-backup-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            await stream_backup_to_file(db, fh)
    except Exception:
        _rm(tmp)
        raise
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return FileResponse(
        tmp, media_type="application/json", filename=f"allin1-backup-{stamp}.json",
        background=BackgroundTask(_rm, tmp),
    )


# ===========================================================================
# Google Drive sync — push the DB snapshot (and, automatically, attachments) to
# the configured Drive folder. Admin-only. Both endpoints degrade gracefully when
# Drive sync is disabled/unconfigured (no crash, clear status).
# ===========================================================================
@router.get("/backup/drive/status")
async def drive_sync_status(user=Depends(require_admin)):
    """Report Drive sync configuration and verify the Service Account connects."""
    from app.services import drive_sync

    return await drive_sync.status()


@router.post("/backup/drive/sync")
async def drive_sync_now(db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """Trigger an immediate full DB snapshot sync to Drive."""
    from app.services import drive_sync

    result = await drive_sync.sync_database_snapshot(db, reason="manual")
    if not result.get("ok"):
        # 409 when sync is simply switched off; 502 when an upstream Drive call failed.
        code = 409 if result.get("skipped") else 502
        raise HTTPException(status_code=code, detail=result)
    return result
