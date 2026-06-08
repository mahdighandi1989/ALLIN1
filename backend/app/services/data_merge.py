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


async def run_data_merge() -> None:
    """Entry point — called once at startup from init_database()."""
    try:
        async with AsyncSessionLocal() as session:
            g = await _merge_guarantors(session)
            f = await _merge_facilities(session)
            await session.commit()
            if g or f:
                logger.info("data-merge: +%d guarantors, %d facilities merged", g, f)
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.warning("data merge skipped: %s", exc)
