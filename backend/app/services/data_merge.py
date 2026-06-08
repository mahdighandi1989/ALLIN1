"""Merge the legacy Excel CRM data into the panel database (idempotent).

Runs at startup after the schema exists. Each step is guarded and safe to re-run:
rows are matched by their stable IDs / account numbers and only inserted or
filled — never blindly duplicated. Source data lives in app/data/merge/*.json
(exported verbatim from the user's Backend_Database workbook).

Phase 1 wave A: guarantors + facility enrichment. Later waves (customer
profiles / KYC, checklist progress, tasks, attachments, journal) extend this.
"""
import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.customer import Customer
from app.models.facility import Facility, FacilityType
from app.models.guarantor import Guarantor
from app.models.crm import CustomerProfile, ChecklistProgress

logger = logging.getLogger(__name__)
_DIR = Path(__file__).resolve().parent.parent / "data" / "merge"

_FT = {
    "overdraft": FacilityType.OVERDRAFT,
    "loan": FacilityType.LOAN,
    "lc": FacilityType.LC,
    "lg": FacilityType.LG,
    "other": FacilityType.OTHER,
}


def _load(name: str) -> list:
    p = _DIR / name
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        logger.warning("merge: could not read %s: %s", name, exc)
        return []


def _map_ftype(raw: str) -> FacilityType:
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


async def _merge_guarantors(session) -> int:
    rows = _load("guarantors.json")
    if not rows:
        return 0
    existing = set((await session.execute(select(Guarantor.id))).scalars().all())
    added = 0
    for r in rows:
        gid = (r.get("guarantor_id") or "").strip()
        if not gid or gid in existing:
            continue
        session.add(Guarantor(
            id=gid,
            account_no=str(r.get("account_no") or "").strip(),
            branch=str(r.get("branch") or "")[:20],
            customer_name=(r.get("customer_name") or "")[:200],
            guarantor_name=(r.get("guarantor_name") or "")[:200],
            guarantor_account=str(r.get("guarantor_account") or "")[:50],
            cheque_no=str(r.get("cheque_no") or "")[:50],
            cheque_amount=r.get("cheque_amount"),
            issuing_bank=(r.get("issuing_bank") or "")[:50],
            fd=(r.get("fd") or "")[:80],
            pim_ref=(r.get("pim_ref") or "")[:80],
            seclist_row=str(r.get("seclist_row") or "")[:20],
            seclist_year=str(r.get("seclist_year") or "")[:10],
            date_added=str(r.get("date_added") or "")[:30],
            created_by=(r.get("user") or "")[:80],
        ))
        existing.add(gid)
        added += 1
    return added


async def _merge_facilities(session) -> int:
    rows = _load("facilities.json")
    if not rows:
        return 0
    # account_no -> customer.id (to link new facilities)
    cmap = {
        str(a): cid for a, cid in
        (await session.execute(select(Customer.account_no, Customer.id))).all()
    }
    existing = {
        f.id: f for f in (await session.execute(select(Facility))).scalars().all()
    }
    touched = 0
    for r in rows:
        fid = (r.get("facility_id") or "").strip()
        if not fid:
            continue
        amt = r.get("amount_num")
        ftype = _map_ftype(r.get("facility_type"))
        name = (r.get("facility_no") or "")[:200]
        cur = (r.get("currency") or "AED")[:3] or "AED"
        fac = existing.get(fid)
        if fac is not None:
            # Fill the real data onto the existing (placeholder) facility.
            fac.facility_type = ftype
            if name:
                fac.name = name
            fac.currency = cur
            fac.is_deleted = False
            if amt is not None:
                fac.amount = amt
            touched += 1
        else:
            cid = cmap.get(str(r.get("account_no")))
            if not cid or amt is None:
                continue  # need a known customer + a real amount to create
            session.add(Facility(
                id=fid, customer_id=cid, name=name, amount=amt, currency=cur,
                facility_type=ftype, risk_rating="medium", is_deleted=False,
            ))
            touched += 1
    return touched


async def _merge_profiles(session) -> int:
    """Merge the comprehensive customer profiles (credit file + KYC)."""
    blob = _load("customer_profiles.json")
    records = blob.get("records") if isinstance(blob, dict) else (blob or [])
    if not records:
        return 0
    existing = set((await session.execute(select(CustomerProfile.account_no))).scalars().all())
    added = 0
    for rec in records:
        acc = str(rec.get("AccountNo") or "").strip()
        if not acc or acc in existing:
            continue
        g = lambda k: (rec.get(k) or "")
        session.add(CustomerProfile(
            account_no=acc,
            customer_name=g("CustomerName")[:200],
            account_type=g("AccountType")[:30],
            branch=g("Branch")[:20],
            business_type=g("BusinessType")[:200],
            rating=g("Rating")[:10],
            customer_status=g("CustomerStatus")[:50],
            trade_license_no=g("TradeLicenseNo")[:80],
            trade_license_expiry=g("TradeLicenseExpiry")[:30],
            passport_no=g("PassportNo")[:80],
            passport_expiry=g("PassportExpiry")[:30],
            emirates_id_no=g("EmiratesIDNo")[:80],
            emirates_id_expiry=g("EmiratesIDExpiry")[:30],
            visa_no=g("VisaNo")[:80],
            visa_expiry=g("VisaExpiry")[:30],
            tenancy_no=g("TenancyNo")[:80],
            tenancy_expiry=g("TenancyExpiry")[:30],
            profile_completeness=str(g("ProfileCompleteness"))[:20],
            updated_by=g("UpdatedBy")[:80],
            last_updated=g("LastUpdated")[:30],
            data_json=json.dumps({k: v for k, v in rec.items() if v not in (None, "")}, ensure_ascii=False),
        ))
        existing.add(acc)
        added += 1
    return added


async def _merge_checklist(session) -> int:
    """Merge the 9-step credit-file workflow progress per customer."""
    rows = _load("checklist_progress.json")
    if not rows:
        return 0
    existing = set((await session.execute(select(ChecklistProgress.account_no))).scalars().all())
    added = 0
    for r in rows:
        acc = str(r.get("account_no") or "").strip()
        if not acc or acc in existing or acc == "Account No":
            continue
        session.add(ChecklistProgress(
            account_no=acc, branch=str(r.get("branch") or "")[:20],
            account_name=(r.get("account_name") or "")[:200], category=(r.get("category") or "")[:40],
            first_action=str(r.get("first_action") or "")[:30], last_action=str(r.get("last_action") or "")[:30],
            total=str(r.get("total") or "")[:10],
            item1=str(r.get("item1") or "")[:10], item2=str(r.get("item2") or "")[:10],
            item3=str(r.get("item3") or "")[:10], item4=str(r.get("item4") or "")[:10],
            item5=str(r.get("item5") or "")[:10], item6=str(r.get("item6") or "")[:10],
            item7=str(r.get("item7") or "")[:10], item8=str(r.get("item8") or "")[:10],
            item9=str(r.get("item9") or "")[:10], last_user=(r.get("last_user") or "")[:80],
        ))
        existing.add(acc)
        added += 1
    return added


async def run_data_merge() -> None:
    """Entry point — called once at startup from init_database()."""
    try:
        async with AsyncSessionLocal() as session:
            g = await _merge_guarantors(session)
            f = await _merge_facilities(session)
            p = await _merge_profiles(session)
            c = await _merge_checklist(session)
            await session.commit()
            if g or f or p or c:
                logger.info(
                    "data-merge: +%d guarantors, %d facilities, +%d profiles, +%d checklists",
                    g, f, p, c,
                )
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.warning("data merge skipped: %s", exc)
