"""Merge the legacy Excel CRM data into the panel database (idempotent).

Runs at startup after the schema exists. Each step is guarded and safe to re-run:
rows are matched by their stable IDs / account numbers and only inserted or
filled — never blindly duplicated. Source data lives in app/data/merge/*.json
(exported verbatim from the user's Backend_Database workbook) plus the gzipped
``customer_listing.jsonl.gz`` (the bank's full core-banking customer export).

Phase 1 wave A: guarantors + facility enrichment. Later waves (customer
profiles / KYC, checklist progress, tasks, attachments, journal) extend this.

The customer-listing waves (``_merge_customer_listing`` /
``_merge_customer_listing_profiles``) import every 6-digit account from the core
banking export — creating a Customer so the panel lists it and a CustomerProfile
as its credit-file "infrastructure" — merging non-destructively into any account
that already exists. See scripts/generate_customer_listing.py for the source map.
"""
import gzip
import json
import logging
from pathlib import Path

from sqlalchemy import insert, or_, select

from app.database import AsyncSessionLocal
from app.models.customer import (
    AccountType,
    Customer,
    CustomerStatus,
    generate_customer_id,
)
from app.models.facility import Facility, FacilityType
from app.models.guarantor import Guarantor
from app.models.security import Security
from app.models.crm import (
    CustomerProfile, ChecklistProgress, CustomTask, Attachment, JournalEntry,
)

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
            # Fill-EMPTY-only, honoring the module contract: the merge must
            # never clobber operator edits, and must never resurrect a
            # facility an operator soft-deleted (this runs on EVERY startup —
            # unconditional writes silently reverted panel changes on each
            # deploy). A soft-deleted facility is left exactly as it is.
            if fac.is_deleted:
                continue
            changed = False
            if not fac.facility_type or getattr(fac.facility_type, "value", fac.facility_type) == "other":
                if ftype and fac.facility_type != ftype:
                    fac.facility_type = ftype
                    changed = True
            if name and not fac.name:
                fac.name = name
                changed = True
            if cur and not fac.currency:
                fac.currency = cur
                changed = True
            if amt is not None and not fac.amount:
                fac.amount = amt
                changed = True
            if changed:
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


async def _insert_missing(session, Model, rows, id_key, build) -> int:
    """Generic: insert rows whose id is not already present (idempotent)."""
    if not rows:
        return 0
    existing = set((await session.execute(select(Model.id))).scalars().all())
    added = 0
    for r in rows:
        rid = str(r.get(id_key) or "").strip()
        if not rid or rid in existing:
            continue
        session.add(build(rid, r))
        existing.add(rid)
        added += 1
    return added


async def _merge_tasks(session) -> int:
    return await _insert_missing(
        session, CustomTask, _load("tasks.json"), "task_id",
        lambda i, r: CustomTask(
            id=i, account_no=str(r.get("account_no") or "")[:50], facility_id=(r.get("facility_id") or "")[:60],
            task_name=(r.get("task_name") or "")[:200], status=(r.get("status") or "")[:30],
            followup_date=str(r.get("followup_date") or "")[:30], notes=r.get("notes") or "",
            priority=(r.get("priority") or "")[:20], created_by=(r.get("created_by") or "")[:80],
            created_date=str(r.get("created_date") or "")[:30], completed_date=str(r.get("completed_date") or "")[:30],
            is_active=str(r.get("is_active") or "")[:5]))


async def _merge_attachments(session) -> int:
    return await _insert_missing(
        session, Attachment, _load("attachments.json"), "attachment_id",
        lambda i, r: Attachment(
            id=i, account_no=str(r.get("account_no") or "")[:50], facility_id=(r.get("facility_id") or "")[:60],
            row_index=str(r.get("row_index") or "")[:10], file_name=(r.get("file_name") or "")[:255],
            original_name=(r.get("original_name") or "")[:255], file_path=r.get("file_path") or "",
            file_size=str(r.get("file_size") or "")[:20], upload_date=str(r.get("upload_date") or "")[:30],
            uploaded_by=(r.get("uploaded_by") or "")[:80], is_shared=str(r.get("is_shared") or "")[:10],
            notes=r.get("notes") or ""))


async def _merge_journal(session) -> int:
    return await _insert_missing(
        session, JournalEntry, _load("journal.json"), "record_id",
        lambda i, r: JournalEntry(
            id=i, account_no=str(r.get("account_no") or "")[:50], branch=str(r.get("branch") or "")[:20],
            account_name=(r.get("account_name") or "")[:200], category=(r.get("category") or "")[:40],
            item=(r.get("item") or "")[:100], status=(r.get("status") or "")[:20], date=str(r.get("date") or "")[:30],
            time=str(r.get("time") or "")[:20], user=(r.get("user") or "")[:80], priority=(r.get("priority") or "")[:20],
            notes=r.get("notes") or "", source=(r.get("source") or "")[:60], action=(r.get("action") or "")[:60]))


async def _merge_securities(session) -> int:
    """Merge the multi-year Securities List register (Retail + Corporate), linked
    to each account by account_no."""
    return await _insert_missing(
        session, Security, _load("securities.json"), "security_id",
        lambda i, r: Security(
            id=i, year=str(r.get("year") or "")[:8], segment=(r.get("segment") or "")[:20],
            date=str(r.get("date") or "")[:30], seq_no=str(r.get("seq_no") or "")[:10],
            branch=str(r.get("branch") or "")[:20], account_no=str(r.get("account_no") or "")[:50],
            customer_name=(r.get("customer_name") or "")[:200], fd=(r.get("fd") or "")[:200],
            guarantor=r.get("guarantor") or "", cheque_no=r.get("cheque_no") or "",
            issuing_bank=r.get("issuing_bank") or "", cheque_amount=r.get("cheque_amount") or "",
            cheque_amount_num=r.get("cheque_amount_num") or 0,
            undertaking=(r.get("undertaking") or "")[:40], guarantee=(r.get("guarantee") or "")[:40],
            credit_facility=(r.get("credit_facility") or "")[:40], original_offer=(r.get("original_offer") or "")[:40],
            property_no=r.get("property_no") or "", mortgage_aed=(r.get("mortgage_aed") or "")[:60],
            remarks=r.get("remarks") or "", stored_date=str(r.get("stored_date") or "")[:30],
            taken_out_date=str(r.get("taken_out_date") or "")[:30]))


# ---------------------------------------------------------------------------
# Full customer listing — the bank's core-banking export of every account.
# Distilled by scripts/generate_customer_listing.py into customer_listing.jsonl.gz
# (6-digit CUSTOMER NUMBER only; 4-digit branch codes mapped to readable labels).
# Merged in two waves so ordering stays correct against the other steps:
#   * customers — runs FIRST, so a Customer exists before facilities link to it.
#   * profiles  — runs AFTER the legacy ``profiles`` step, so the richer legacy
#                 KYC is created first and the listing only fills the gaps.
# Both stream the file record-by-record (memory-safe on the 512MB instance) and
# upsert non-destructively by account_no: new rows are inserted in chunks and
# existing rows only get their EMPTY columns filled (real data never clobbered).
# ---------------------------------------------------------------------------
_LISTING_JSONL_GZ = "customer_listing.jsonl.gz"
_VALID_ATYPE = {t.value for t in AccountType}
_INSERT_CHUNK = 2000


def _iter_listing():
    """Yield the listing's records one at a time from the gzipped JSONL file.

    Streaming (rather than loading all ~44k dicts at once) keeps the merge well
    within the 512MB production instance: only one record — plus the current
    insert batch — is ever held in memory. Yields nothing if the file is absent
    or unreadable.
    """
    path = _DIR / _LISTING_JSONL_GZ
    if not path.exists():
        return
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)
    except Exception as exc:  # pragma: no cover - corrupt/truncated file
        logger.warning("merge: could not read customer listing: %s", exc)
        return


def _atype(rec: dict) -> str:
    a = str(rec.get("account_type") or "retail").lower()
    return a if a in _VALID_ATYPE else "retail"


def _customer_branch(rec: dict):
    return rec.get("branch_label") or rec.get("branch_code") or None


def _fill_empty(obj, values: dict) -> bool:
    """Set attrs from ``values`` only where the current attribute is empty.

    Implements the agreed non-destructive merge: data already on the row is never
    overwritten — the listing fills blanks only. Returns True if anything changed.
    """
    changed = False
    for key, val in values.items():
        if isinstance(val, str):
            val = val.strip()
        if not val:
            continue
        cur = getattr(obj, key, None)
        if cur is None or (isinstance(cur, str) and cur.strip() == ""):
            setattr(obj, key, val)
            changed = True
    return changed


def _profile_fill_values(rec: dict) -> dict:
    """The CustomerProfile columns the listing can populate (None when blank)."""

    def g(key, limit):
        v = (rec.get(key) or "").strip()
        return v[:limit] if v else None

    return {
        "customer_name": g("name", 200),
        "account_type": g("entity_type", 30),
        "branch": g("branch_code", 20),
        "customer_status": g("status_desc", 50),
        "passport_no": g("passport_no", 80),
        "emirates_id_no": g("national_id", 80),
        "trade_license_no": g("trade_license_no", 80),
        "passport_nationality": g("nationality", 80),
    }


def _profile_data_json(rec: dict) -> str:
    """Keep the listing's extra attributes (nationality, PEP, BRM, …) verbatim."""
    keep = {
        k: rec.get(k)
        for k in (
            "nationality", "pep_status", "rr_pep", "entity_type", "customer_type",
            "brm_code", "date_added", "status_desc", "branch_code", "branch_label",
            "email", "mobile",
        )
        if rec.get(k)
    }
    keep["source"] = "customer_listing"
    return json.dumps(keep, ensure_ascii=False)


async def _branchless_accounts(session, model) -> set:
    """account_nos of rows still missing a branch — the only ones the fill pass
    must touch. Tiny in steady state (listing rows all carry a branch), so we can
    stash just these records while streaming instead of holding all ~44k."""
    return set((await session.execute(
        select(model.account_no).where(
            or_(model.branch.is_(None), model.branch == "")
        )
    )).scalars().all())


async def _load_in_chunks(session, model, account_nos):
    """Yield ``model`` rows for a (small) set of account_nos, 500 at a time, so a
    large fill set can never build one giant IN-clause or result set."""
    accs = list(account_nos)
    for i in range(0, len(accs), 500):
        rows = (await session.execute(
            select(model).where(model.account_no.in_(accs[i : i + 500]))
        )).scalars().all()
        for row in rows:
            yield row


async def _merge_customer_listing(session) -> int:
    """Wave 1 — make every 6-digit listed account a Customer so the panel lists it.

    Streams the listing record-by-record (memory-safe on a 512MB instance): brand
    new accounts are inserted in chunks; accounts that already exist only get their
    *empty* columns filled. Idempotent — a re-run inserts nothing new.
    """
    existing = set((await session.execute(select(Customer.account_no))).scalars().all())
    need_fill = await _branchless_accounts(session, Customer)
    batch: list = []
    fills: dict = {}
    created = 0
    for rec in _iter_listing():
        acc = rec.get("account_no")
        if not acc:
            continue
        if acc in existing:
            if acc in need_fill:
                fills[acc] = rec  # pre-existing + incomplete → fill it later
            continue
        existing.add(acc)  # guard against any in-file duplicate
        batch.append({
            "id": generate_customer_id(),
            "account_no": acc,
            "name": (rec.get("name") or f"Account {acc}")[:200],
            "name_ar": rec.get("name_ar") or None,
            "account_type": AccountType(_atype(rec)),
            "status": CustomerStatus.ACTIVE,
            "email": rec.get("email") or None,
            "phone": rec.get("mobile") or None,
            "mobile": rec.get("mobile") or None,
            "branch": _customer_branch(rec),
            "is_deleted": False,
        })
        if len(batch) >= _INSERT_CHUNK:
            await session.execute(insert(Customer), batch)
            await session.commit()  # commit per chunk: bound the txn + persist progress
            created += len(batch)
            batch = []
    if batch:
        await session.execute(insert(Customer), batch)
        await session.commit()
        created += len(batch)

    # Non-destructive fill for the few pre-existing, branch-less accounts.
    filled = 0
    async for cust in _load_in_chunks(session, Customer, fills.keys()):
        rec = fills.get(cust.account_no)
        if rec and _fill_empty(cust, {
            "name": rec.get("name"),
            "name_ar": rec.get("name_ar"),
            "branch": _customer_branch(rec),
            "email": rec.get("email"),
            "mobile": rec.get("mobile"),
            "phone": rec.get("mobile"),
        }):
            filled += 1
    if filled:
        await session.commit()
    return created + filled


async def _merge_customer_listing_profiles(session) -> int:
    """Wave 2 — ensure every listed account has credit-file 'infrastructure'
    (a CustomerProfile). Streams the listing (memory-safe): creates the missing
    profiles and fills the empty fields the listing knows (nationality, KYC numbers,
    branch, PEP); never overwrites the richer legacy profile the earlier
    ``profiles`` step may have created.
    """
    existing = set(
        (await session.execute(select(CustomerProfile.account_no))).scalars().all()
    )
    need_fill = await _branchless_accounts(session, CustomerProfile)
    batch: list = []
    fills: dict = {}
    created = 0
    for rec in _iter_listing():
        acc = rec.get("account_no")
        if not acc:
            continue
        if acc in existing:
            if acc in need_fill:
                fills[acc] = rec
            continue
        existing.add(acc)
        row = _profile_fill_values(rec)
        row["account_no"] = acc
        row["data_json"] = _profile_data_json(rec)
        batch.append(row)
        if len(batch) >= _INSERT_CHUNK:
            await session.execute(insert(CustomerProfile), batch)
            await session.commit()  # commit per chunk: bound the txn + persist progress
            created += len(batch)
            batch = []
    if batch:
        await session.execute(insert(CustomerProfile), batch)
        await session.commit()
        created += len(batch)

    # Fill empties on the few pre-existing, branch-less profiles (legacy rows).
    filled = 0
    async for prof in _load_in_chunks(session, CustomerProfile, fills.keys()):
        rec = fills.get(prof.account_no)
        if rec and _fill_empty(prof, _profile_fill_values(rec)):
            filled += 1
    if filled:
        await session.commit()
    return created + filled


_STEPS = [
    ("customer_listing", _merge_customer_listing),
    ("guarantors", _merge_guarantors),
    ("facilities", _merge_facilities),
    ("profiles", _merge_profiles),
    ("customer_listing_profiles", _merge_customer_listing_profiles),
    ("checklists", _merge_checklist),
    ("tasks", _merge_tasks),
    ("attachments", _merge_attachments),
    ("journal", _merge_journal),
    ("securities", _merge_securities),
]


async def run_data_merge() -> dict:
    """Run every merge step INDEPENDENTLY and return a per-step report.

    Each step gets its own session + commit + try/except, so a single failing
    step (e.g. a constraint hiccup) can never silently skip the others — the
    bug where the whole merge was wrapped in one try/except and one early error
    abandoned the rest (leaving facilities un-filled in production).
    """
    report: dict = {}
    for name, fn in _STEPS:
        try:
            async with AsyncSessionLocal() as session:
                n = await fn(session)
                await session.commit()
            report[name] = n
        except Exception as exc:  # pragma: no cover - depends on live DB
            logger.warning("data-merge step %s failed: %s", name, exc, exc_info=True)
            # Surface the exception TYPE + a generous slice of the message so the
            # /run-merge report alone is enough to diagnose a live failure.
            report[name] = f"error: {type(exc).__name__}: {str(exc)[:300]}"
    logger.info("data-merge report: %s", report)
    return report
