"""گزارش خلاصهٔ پروندهٔ حقوقی — wired at /api/case-reports.

Saved legal case-file summary reports. Deliberately the same shape as
``routers/letters.py`` — same two buckets (under an account, or general), same
per-report values/layout/labels, same mojibake repair on read AND write, same
attachment story, same audit trail, same soft delete — because the owner asked for
this report to carry «تمام قابلیت‌ها و گزینه‌ها» that the official letters carry.
Where the behaviour is identical the code is deliberately parallel rather than
cleverly shared, so a change to letters can never silently change reports.

What is NOT parallel is ``/prefill``: the report asks for facts the database
already holds (partners, facilities, collateral), and typing them again by hand is
how they drift. Prefill READS only — it never writes and never overwrites a saved
report; the page offers the values and the user keeps or edits them.
"""
import json
import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.case_report import CaseReport, generate_case_report_id
from app.routers.auth import get_current_active_user, require_editor
from app.services import mojibake
from app.services.audit import record_audit
from app.services.customer_link import ensure_customer

logger = logging.getLogger("app.case_reports")

router = APIRouter(tags=["case-reports"], dependencies=[Depends(get_current_active_user)])

# Every repeating section, and the column that holds it. Listed once so the
# schema, the apply step and the read step can never disagree about which
# sections exist — adding section 12 means adding one line here.
TABLE_FIELDS = (
    "partners", "facilities_granted", "facilities_unsettled", "collections",
    "collaterals", "approvals", "collateral_actions", "discounted_cheques",
    "commitments",
)

# Scalar fields the client may set. Kept explicit (not `__table__.columns`) so a
# future internal column is never silently writable from the browser.
SCALAR_FIELDS = (
    "title", "letter_date", "letter_no", "classification", "recipient_name",
    "recipient_title", "subject", "subject_entity", "subject_account", "subject_branch",
    "ref_letter_no", "ref_letter_date", "ref_letter_dept", "basis_letter_no",
    "basis_letter_date", "company_name", "established_year", "licence_no", "free_zone",
    "activity", "is_active", "manager_name", "account_open_date", "first_facility_year",
    "company_summary", "stagnation_date", "stagnation_balance", "classification_date",
    "classification_balance", "stagnation_note", "offbalance_date", "books_note",
    "books_principal", "books_overdue_interest", "books_aed_costs", "books_total",
    "books_provisions", "books_irr_costs", "court_principal", "court_interest",
    "court_interest_rate", "court_interest_from", "court_legal_costs", "court_collected",
    "court_total", "collections_total", "commitments_note", "judgment_action_date",
    "judgment_final_date", "judgment_sent_iran_date", "other_notes", "branch_name",
    "branch_code", "prepared_by",
)

# The three verbatim totals that also get a parsed numeric mirror.
NUM_MIRRORS = (
    ("books_total", "books_total_num"),
    ("court_total", "court_total_num"),
    ("collections_total", "collections_total_num"),
)

_MAXLEN = {c.name: getattr(c.type, "length", None) for c in CaseReport.__table__.columns}


def _dumps(v: Any) -> Optional[str]:
    return json.dumps(v, ensure_ascii=False) if v is not None else None


def _loads(s: Optional[str]) -> Any:
    try:
        return json.loads(s) if s else None
    except Exception:
        return None


def parse_amount(raw: Any) -> Optional[Decimal]:
    """Bank-Persian money text → a number, or None when it genuinely isn't one.

    The source documents write amounts in ways no locale parses. The one that
    matters most is the FRACTION-FIRST form: a right-to-left page renders
    «22.645/95» so that text extraction hands us ``95/22.645`` — the two digits
    before the slash are the decimal part, and the dots are thousands separators.
    So ``95/22.645`` is 22,645.95 and ``65/ 113,004`` is 113,004.65, not sixty-five
    million. A leading ``-/`` is the round-figure marker («-/312,240» = 312,240),
    Persian and Arabic-Indic digits appear freely, and the currency word may be
    glued to the number («15/540.412درهم»).

    Returns **None**, not 0, when nothing can be read. A total that could not be
    parsed is not a total of zero, and a register that summed it as zero would
    quietly under-report the bank's own claim
    (experiences/a-monitor-must-distinguish-unmeasured-from-zero.md).
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float, Decimal)):
        return Decimal(str(raw))
    s = str(raw).strip()
    if not s:
        return None
    s = s.translate({ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})
    s = s.translate({ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")})
    for junk in ("درهم", "ریال", "دلار", "AED", "aed", "USD", "IRR",
                 "\u200c", "\u200f", "\u200e", "\xa0"):
        s = s.replace(junk, "")
    s = s.replace("-/", "").replace("/-", "").strip()
    s = "".join(ch for ch in s if ch.isdigit() or ch in ".,/ ").strip()
    if not any(ch.isdigit() for ch in s):
        return None

    def _digits(part: str) -> str:
        """Drop thousands separators, keeping a trailing 1-2 digit group as decimals."""
        part = part.replace(" ", "").replace(",", "")
        if part.count(".") == 1:
            head, _, tail = part.partition(".")
            if len(tail) in (1, 2) and head:   # 1.5 / 1.50 → a real decimal
                return head + "." + tail
        return part.replace(".", "")

    frac_first = re.match(r"^(\d{1,2})\s*/\s*([\d.,\s]+)$", s)
    if frac_first:
        whole = _digits(frac_first.group(2)).replace(".", "")
        if not whole:
            return None
        s = f"{whole}.{frac_first.group(1)}"
    else:
        s = _digits(s.replace("/", ""))
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _values(r: CaseReport) -> Any:
    """The report's presentation values, with PDF-font mojibake repaired on read.

    Same contract as ``letters._values``: repair on READ so an already-garbled
    report shows correctly with nothing to press, and on WRITE so it becomes
    permanently correct the next time it is saved.
    """
    v = _loads(r.values_json)
    if v is None:
        return None
    repaired, n = mojibake.repair_json(v)
    if n:
        logger.info("case report %s: repaired %d garbled text run(s) on read", r.id, n)
    return repaired


def _tables(r: CaseReport) -> dict:
    return {f: _loads(getattr(r, f"{f}_json")) for f in TABLE_FIELDS}


class CaseReportSummary(BaseModel):
    id: str
    account_no: Optional[str] = None
    category: str
    title: Optional[str] = None
    subject: Optional[str] = None
    subject_entity: Optional[str] = None
    subject_account: Optional[str] = None
    subject_branch: Optional[str] = None
    letter_no: Optional[str] = None
    letter_date: Optional[str] = None
    books_total: Optional[str] = None
    court_total: Optional[str] = None
    collections_total: Optional[str] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class CaseReportFull(CaseReportSummary):
    fields: dict = {}
    tables: dict = {}
    values: Any = None
    layout: Any = None
    labels: Any = None


class CaseReportSave(BaseModel):
    account_no: Optional[str] = Field(default=None, max_length=50)
    general: bool = False
    fields: dict = Field(default_factory=dict)
    tables: dict = Field(default_factory=dict)
    values: Any = None
    layout: Any = None
    labels: Any = None


def _full(r: CaseReport) -> CaseReportFull:
    out = CaseReportFull.model_validate(r)
    out.fields = {f: getattr(r, f) for f in SCALAR_FIELDS}
    out.tables = _tables(r)
    out.values, out.layout, out.labels = _values(r), _loads(r.layout_json), _loads(r.labels_json)
    return out


@router.get("/", response_model=List[CaseReportSummary])
async def list_case_reports(
    db: AsyncSession = Depends(get_db),
    account_no: Optional[str] = Query(None),
    general: bool = Query(False),
):
    base = select(CaseReport).where(CaseReport.is_deleted == False)  # noqa: E712
    if general:
        base = base.where(CaseReport.category == "general")
    elif account_no:
        base = base.where(CaseReport.account_no == account_no)
    rows = (await db.execute(
        base.order_by(CaseReport.updated_at.desc().nullslast(), CaseReport.created_at.desc()).limit(500)
    )).scalars().all()
    return [CaseReportSummary.model_validate(r) for r in rows]


@router.get("/prefill")
async def prefill(account_no: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    """What the database ALREADY knows about this account, offered to a new report.

    Read-only by design: it never writes and never touches a saved report. Typing
    partners and facilities a second time is how the report and the profile drift
    apart, so the page offers these and the user keeps or edits them.

    NOTE — this literal path must stay ABOVE «/{report_id}». A literal path
    declared after a path parameter is never reached; FastAPI would match
    «prefill» as a report id and answer with a 404-shaped lookup
    (experiences/a-literal-route-must-precede-its-wildcard.md).
    """
    from app.models.crm import CustomerProfile
    from app.models.customer import Customer
    from app.models.facility import Facility
    from app.models.guarantor import Guarantor
    from app.models.profile_entities import MortgagedProperty, Partner
    from app.models.security import Security

    acc = account_no.strip()
    out: dict = {"account_no": acc, "found": False, "fields": {}, "tables": {}, "sources": {}}

    cust = (await db.execute(
        select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False)  # noqa: E712
    )).scalar_one_or_none()
    prof = (await db.execute(
        select(CustomerProfile).where(CustomerProfile.account_no == acc)
    )).scalar_one_or_none()

    if cust is not None or prof is not None:
        out["found"] = True
        name = (cust.name if cust is not None else None) or getattr(prof, "customer_name", "") or ""
        branch = (cust.branch if cust is not None else None) or getattr(prof, "branch", "") or ""
        out["fields"] = {
            "company_name": name,
            "subject_entity": name,
            "subject_account": acc,
            "subject_branch": branch,
            "branch_name": branch,
        }
        if prof is not None:
            # Only facts the profile actually holds. Nothing here is DERIVED:
            # an establishment year is not guessed from a licence date, and an
            # account-opening date is not guessed from anything — a report that
            # invents either is worse than one with a blank the writer fills in.
            out["fields"].update({
                "licence_no": prof.trade_license_no or "",
                "activity": prof.business_type or "",
                "established_year": prof.established_since or "",
                "account_open_date": prof.relationship_date or "",
            })
            out["sources"]["profile"] = 1
        if cust is not None:
            out["sources"]["customer"] = 1

    partners = (await db.execute(
        select(Partner).where(Partner.account_no == acc, Partner.is_deleted == False)  # noqa: E712
    )).scalars().all()
    # The manager named in §1's narrative is whichever partner holds a managing
    # role. If none of them does, the blank stays blank rather than naming the
    # first partner and hoping.
    mgr = next((x for x in partners
                if any(w in (x.role or "").lower()
                       for w in ("مدیر", "manager", "director", "signator"))), None)
    if mgr is not None:
        out["fields"]["manager_name"] = mgr.name or ""

    out["tables"]["partners"] = [{
        "name": p.name or "",
        "national_id": p.national_id or "",
        "share": " — ".join(x for x in [(p.share or ""), (p.nationality or "")] if x),
        "role": p.role or "",
    } for p in partners]
    out["sources"]["partners"] = len(partners)

    facilities = []
    if cust is not None:
        facilities = (await db.execute(
            select(Facility).where(Facility.customer_id == cust.id, Facility.is_deleted == False)  # noqa: E712
        )).scalars().all()
    out["tables"]["facilities_granted"] = [{
        "type": f.name or (getattr(f.facility_type, "value", None) or str(f.facility_type or "")),
        "amount": f"{f.amount:,.0f} درهم" if f.amount is not None else "",
        "grant_date": f.start_date.strftime("%d/%m/%Y") if f.start_date else "",
        "rate": f"{f.interest_rate:g}%" if f.interest_rate is not None else "",
    } for f in facilities]
    out["sources"]["facilities"] = len(facilities)

    # §7 collateral comes from three registers that each hold part of the picture.
    collateral: list[dict] = []
    for g in (await db.execute(
        select(Guarantor).where(Guarantor.account_no == acc, Guarantor.is_deleted == False)  # noqa: E712
    )).scalars().all():
        collateral.append({
            "type": f"چک از {g.guarantor_name}" if g.guarantor_name else "چک ضمانتی",
            "reference_no": g.cheque_no or "",
            "amount": f"-/{g.cheque_amount:,.0f}" if g.cheque_amount is not None else "",
        })
    for s in (await db.execute(
        select(Security).where(Security.account_no == acc, Security.is_deleted == False)  # noqa: E712
    )).scalars().all():
        collateral.append({
            "type": (s.guarantor or s.fd or "چک ضمانتی"),
            "reference_no": s.cheque_no or "",
            "amount": s.cheque_amount or "",
        })
    for mp in (await db.execute(
        select(MortgagedProperty).where(MortgagedProperty.account_no == acc,
                                        MortgagedProperty.is_deleted == False)  # noqa: E712
    )).scalars().all():
        collateral.append({
            "type": f"وثیقهٔ ملکی رهنی{(' در ' + mp.country) if mp.country else ''}",
            "reference_no": f"پلاک ثبتی {mp.plate_no}" if mp.plate_no else (mp.mortgage_deed_no or ""),
            "amount": (f"{mp.mortgage_amount:,.0f} {mp.mortgage_currency or ''}".strip()
                       if mp.mortgage_amount is not None else ""),
        })
    out["tables"]["collaterals"] = collateral
    out["sources"]["collateral"] = len(collateral)
    return out


@router.get("/{report_id}", response_model=CaseReportFull)
async def get_case_report(report_id: str, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(CaseReport).where(
        CaseReport.id == report_id, CaseReport.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if r is None:
        raise HTTPException(status_code=404, detail="Case report not found")
    return _full(r)


async def _apply(r: CaseReport, p: CaseReportSave, db, user) -> None:
    acc = (p.account_no or "").strip()
    if acc and not p.general:
        await ensure_customer(db, acc, None)   # auto-create the profile, like letters do
        r.account_no, r.category = acc, "account"
    else:
        r.account_no, r.category = None, "general"

    for name in SCALAR_FIELDS:
        if name not in p.fields:
            continue
        raw = p.fields.get(name)
        val = "" if raw is None else str(raw).strip()
        limit = _MAXLEN.get(name)
        if limit:
            val = val[:limit]
        setattr(r, name, val or None)

    for name in TABLE_FIELDS:
        if name not in p.tables:
            continue
        rows = p.tables.get(name)
        rows = rows if isinstance(rows, list) else []
        # Repair PDF-font mojibake on WRITE so a report built from a faulty PDF can
        # never be STORED garbled — the same contract letters keep.
        rows, n = mojibake.repair_json(rows)
        if n:
            logger.info("case report %s: repaired %d garbled run(s) in %s", r.id, n, name)
        setattr(r, f"{name}_json", _dumps(rows))

    for text_col, num_col in NUM_MIRRORS:
        parsed = parse_amount(getattr(r, text_col))
        # None means «could not read it», which must not be written as 0.
        setattr(r, num_col, parsed)

    if p.values is not None:
        vals, n = mojibake.repair_json(p.values)
        if n:
            logger.info("case report %s: repaired %d garbled run(s) on save", r.id, n)
        r.values_json = _dumps(vals)
    if p.layout is not None:
        r.layout_json = _dumps(p.layout)
    if p.labels is not None:
        r.labels_json = _dumps(p.labels)
    r.updated_by = getattr(user, "username", "") or ""


def _label(r: CaseReport) -> str:
    return r.title or r.subject_entity or r.subject or r.id


@router.post("/", response_model=CaseReportFull, status_code=201)
async def create_case_report(payload: CaseReportSave, request: Request,
                             db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    r = CaseReport(id=generate_case_report_id(), created_by=getattr(user, "username", "") or "")
    await _apply(r, payload, db, user)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    await record_audit(action="create", entity_type="case_report", entity_id=r.id,
                       account_no=r.account_no,
                       detail=f"ذخیرهٔ گزارش خلاصهٔ پرونده — {_label(r)}"
                              f"{'' if r.account_no else ' (عمومی)'}",
                       user=user, request=request, db=db)
    return _full(r)


@router.patch("/{report_id}", response_model=CaseReportFull)
async def update_case_report(report_id: str, payload: CaseReportSave, request: Request,
                             db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    r = (await db.execute(select(CaseReport).where(
        CaseReport.id == report_id, CaseReport.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if r is None:
        raise HTTPException(status_code=404, detail="Case report not found")
    await _apply(r, payload, db, user)
    await db.commit()
    await db.refresh(r)
    await record_audit(action="update", entity_type="case_report", entity_id=r.id,
                       account_no=r.account_no,
                       detail=f"ویرایشِ گزارش خلاصهٔ پرونده — {_label(r)}",
                       user=user, request=request, db=db)
    return _full(r)


@router.get("/{report_id}/attachments")
async def list_case_report_attachments(report_id: str, db: AsyncSession = Depends(get_db)):
    """The report's uploaded enclosures (پیوست‌ها).

    Uploads go through the shared /api/crm/attachments endpoint with
    facility_id=CASE-<report id>, exactly as letters use LTR-<letter id>: the files
    live in Drive with a disk fallback AND appear under the customer profile's
    attachments, because they carry the same account_no.
    """
    from app.models.crm import Attachment

    rows = (await db.execute(
        select(Attachment).where(Attachment.facility_id == f"CASE-{report_id}")
        .order_by(Attachment.upload_date.desc())
    )).scalars().all()
    return [{
        "id": a.id, "account_no": a.account_no, "original_name": a.original_name,
        "file_size": a.file_size, "upload_date": a.upload_date, "uploaded_by": a.uploaded_by,
        "storage": "drive" if (a.drive_file_id or "") else "disk",
    } for a in rows]


@router.delete("/{report_id}", status_code=204)
async def delete_case_report(report_id: str, request: Request,
                             db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    r = (await db.execute(select(CaseReport).where(
        CaseReport.id == report_id, CaseReport.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if r is None:
        raise HTTPException(status_code=404, detail="Case report not found")
    r.is_deleted = True            # soft delete — recoverable from the recycle bin
    await db.commit()
    await record_audit(action="delete", entity_type="case_report", entity_id=r.id,
                       account_no=r.account_no,
                       detail=f"حذفِ گزارش خلاصهٔ پرونده — {_label(r)}",
                       user=user, request=request, db=db)
    return None
