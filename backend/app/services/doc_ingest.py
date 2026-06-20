"""AI document-ingestion core.

Sends an uploaded file (PDF / image / …) to a vision/document model with a strong
extraction prompt, parses the strict JSON it returns, and persists each customer's
data — deduped — exactly like the rest of the app:
  • scalar facts → promoted profile columns + data_json (keyed, overwrite-in-place)
  • a credit-review row when the doc is a committee approval (deduped per date)
  • guarantors via upsert (which feeds the cross-account relationship graph)
  • a page→document map kept under the profile + on the attachment link

The file itself is stored in Google Drive by the caller (so the main DB stays
light); only metadata/links are kept in the DB.
"""
from __future__ import annotations

import json
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, AccountType
from app.models.crm import CustomerProfile
from app.models.guarantor import Guarantor
from app.models.profile_entities import MortgagedProperty
from app.services.customer_link import ensure_customer

# ---------------------------------------------------------------------------
# Schema-driven field registry. The list of facts the model is asked to extract
# (and that ``persist_customer`` writes to real columns) is DERIVED from the live
# ``CustomerProfile`` schema — so when a new column is added to the model later,
# it is automatically asked-for and persisted with NO change here. Only the few
# non-extractable columns below are excluded.
# ---------------------------------------------------------------------------
_PROFILE_SKIP_COLS = {
    # identity / handled at the customer level
    "account_no", "customer_name", "account_type", "branch",
    # housekeeping / computed
    "rating", "customer_status", "profile_completeness", "updated_by",
    "last_updated", "data_json", "created_at",
    # per-document file paths (populated by the upload feature, not from content)
    "trade_license_doc", "passport_doc", "emirates_id_doc", "visa_doc", "tenancy_doc",
    # officer-only free-text notes — never auto-filled by the model
    "trade_license_remarks", "passport_remarks", "emirates_id_remarks",
}
# Friendlier key the model is more likely to emit  ->  real column it maps to.
_FIELD_ALIASES = {"nationality": "passport_nationality"}
_COL_TO_FRIENDLY = {v: k for k, v in _FIELD_ALIASES.items()}


def extractable_profile_fields() -> list[str]:
    """The field keys the model should fill, derived live from the CustomerProfile
    schema (with a friendly alias where one exists). Adding a column to the model
    automatically adds it here — no prompt or persist edits needed."""
    out: list[str] = []
    for c in CustomerProfile.__table__.columns:
        if c.name in _PROFILE_SKIP_COLS:
            continue
        out.append(_COL_TO_FRIENDLY.get(c.name, c.name))
    return out


def _build_fields_block() -> str:
    """Pretty 3-per-line JSON skeleton of the extractable fields for the prompt."""
    parts = [f'"{k}": ""' for k in extractable_profile_fields()]
    return ",\n".join("        " + ", ".join(parts[i:i + 3]) for i in range(0, len(parts), 3))


def build_extraction_prompt() -> str:
    """Assemble the extraction prompt with the field list taken from the schema."""
    return (
        """You are a meticulous UAE banking credit-file analyst. Read the ATTACHED document(s) end to end (every page) and extract the data for the bank's customer database.

A single file MAY contain data for MORE THAN ONE customer/account (e.g. a borrower plus guarantors, or several approvals). Detect every distinct account and attribute each fact to the CORRECT account — never mix customers.

Return STRICT JSON ONLY (no markdown, no commentary), exactly this shape:
{
  "customers": [
    {
      "account_no": "<6-digit core account number>",
      "account_display": "<full as printed, e.g. 2624-115524-011>",
      "name": "<customer/company name>",
      "account_type": "retail" | "corporate",
      "branch": "<branch name and/or code>",
      "fields": {
"""
        + _build_fields_block()
        + """
      },
      "guarantors": [ {"name": "", "account": "", "branch": ""} ],
      "properties": [ {"prop_type": "", "address": "", "city": "", "country": "",
                       "valuation": "", "valuation_currency": "AED", "mortgage_amount": "", "mortgage_currency": "AED",
                       "plate_no": "", "mortgage_deed_no": "", "mortgage_date": "", "insurance_expiry": ""} ],
      "review": {
        "date_of_review": "", "credit_application_no": "", "purpose": "",
        "proposed_rating": "", "rating_notes": "", "cru_recommendation": ""
      }
    }
  ],
  "documents": [
    {"pages": "1-2", "type": "Trade License", "customer_account": "<6-digit>", "summary": "<one line>"}
  ]
}

Rules:
- Extract EVERY field listed under "fields" that the document actually contains — including the small ones officers often miss: every ID's issue date AND expiry date, visa number/issue/expiry/type, tenancy number/issue/expiry/address, whether the Emirates ID is "golden" (Yes/No), etc.
- Only include fields you actually find; omit unknowns (do NOT invent values).
- Always capture the customer's full legal NAME exactly as printed.
- Capture each ID document's NUMBER together with its ISSUE and EXPIRY dates.
- "nationality" ONLY if it is explicitly printed — never guess or assume it.
- Dates as printed (DD/MM/YYYY is fine); a RENEWED document's later date should be reported so the record updates.
- "account_no" is the 6-digit core (the middle group of 2624-115524-011 is 115524).
- Numbers as plain digits (no thousands separators) where possible.
- "documents" must list, for EVERY page or page-range, which document it is and which account it belongs to.
- Output ONLY the JSON object.""")


# Built once from the current schema (the model is fully defined at import).
EXTRACTION_PROMPT = build_extraction_prompt()


def parse_model_json(text: str) -> dict:
    """Best-effort parse of the model's JSON reply (tolerates code fences/prose)."""
    if not text:
        return {}
    t = text.strip()
    t = re.sub(r"^```(?:json)?", "", t).strip()
    if t.endswith("```"):
        t = t[:-3].strip()
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        t = t[i:j + 1]
    try:
        out = json.loads(t)
        return out if isinstance(out, dict) else {}
    except Exception:
        return {}


def _newer_or_empty(new: str, old: str) -> bool:
    """True if ``new`` should replace ``old`` for a date field: old empty, or new
    is a later (renewed) date. Unparseable new → keep old (don't clobber)."""
    if not (new or "").strip():
        return False
    if not (old or "").strip():
        return True
    try:
        from dateutil import parser as _dp
        nd = _dp.parse(new, dayfirst=True, fuzzy=True).date()
    except Exception:
        return False
    try:
        from dateutil import parser as _dp
        od = _dp.parse(old, dayfirst=True, fuzzy=True).date()
    except Exception:
        return True
    return nd >= od


_KYC_DATE_COLS = {
    "trade_license_issue", "trade_license_expiry", "passport_issue", "passport_expiry",
    "emirates_id_issue", "emirates_id_expiry", "visa_expiry", "tenancy_expiry",
}


def _acc_of(cust: dict) -> str:
    acc = str(cust.get("account_no") or "").strip()
    if re.fullmatch(r"\d{6}", acc):
        return acc
    for src in (acc, str(cust.get("account_display") or "")):
        m = re.search(r"\b(\d{6})\b", src)
        if m:
            return m.group(1)
    return acc


def _apply_extracted_fields(cp, fields: dict) -> None:
    """Write extracted scalars onto the profile, SCHEMA-DRIVEN: any key matching a
    CustomerProfile column (directly or via alias) is promoted to that column.

    Write policy (smart, no blind overwrite):
      • KYC document dates (issue/expiry) UPDATE on renewal — a later date wins, so
        a renewed passport/EID/visa/tenancy refreshes the record.
      • everything else is fill-empty — a possibly-wrong extraction never clobbers
        a value an officer has already curated.
    """
    cols = {c.name: c for c in CustomerProfile.__table__.columns}
    for key, v in (fields or {}).items():
        if v in (None, ""):
            continue
        col = _FIELD_ALIASES.get(key, key)
        if col in _PROFILE_SKIP_COLS or col not in cols:
            continue  # not a writable column → stays in data_json only
        cur = getattr(cp, col, "")
        cur = cur.strip() if isinstance(cur, str) else (cur or "")
        take = _newer_or_empty(str(v), str(cur)) if col in _KYC_DATE_COLS else (not cur)
        if take:
            ml = getattr(getattr(cols[col], "type", None), "length", None)
            setattr(cp, col, str(v)[:ml] if ml else str(v))


async def persist_customer(db: AsyncSession, cust: dict, username: str, source: str = "import_ai") -> dict:
    """Apply one extracted customer dict to the DB (deduped). Returns a summary."""
    from app.routers.crm import _upsert_credit_review  # shared helper

    acc = _acc_of(cust)
    if not acc:
        return {"ok": False, "reason": "no_account"}
    name = (cust.get("name") or "").strip() or None
    customer = await ensure_customer(db, acc, name)
    at = str(cust.get("account_type") or "").lower()
    if customer is not None and at in ("retail", "corporate", "sme"):
        customer.account_type = AccountType(at)
    if customer is not None and name and (not customer.name or customer.name.strip() in ("", acc)):
        customer.name = name[:200]
    branch = (cust.get("branch") or "").strip()
    if customer is not None and branch and not (customer.branch or "").strip():
        customer.branch = branch[:100]

    fields = {k: v for k, v in (cust.get("fields") or {}).items() if v not in (None, "")}

    cp = (await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))).scalar_one_or_none()
    if cp is None:
        cp = CustomerProfile(account_no=acc, customer_name=name)
        db.add(cp)
    # Schema-driven: promote EVERY recognised field to its real column (identity,
    # KYC docs incl. issue dates / visa type / tenancy address / golden EID, and
    # the credit scalars). Adding a new column to the model later is picked up here
    # automatically — no edit needed.
    _apply_extracted_fields(cp, fields)
    try:
        data = json.loads(cp.data_json) if cp.data_json else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    for k, v in fields.items():
        data[str(k)] = v  # keyed → no duplicates on re-import
    cp.data_json = json.dumps(data, ensure_ascii=False)
    cp.last_updated = date.today().isoformat()
    cp.updated_by = username

    review = {k: v for k, v in (cust.get("review") or {}).items() if v not in (None, "")}
    if review:
        review.setdefault("customer_name", name)
        if at:
            review.setdefault("account_type", at)
        await _upsert_credit_review(db, acc, review, source, username)

    g_added = g_updated = 0
    for g in (cust.get("guarantors") or []):
        gname = (g.get("name") or "").strip()
        gacc = (g.get("account") or "").strip()
        if not gname:
            continue
        if gacc:
            await ensure_customer(db, gacc, gname)
        row = None
        if gacc:
            row = (await db.execute(select(Guarantor).where(
                Guarantor.account_no == acc, Guarantor.guarantor_account == gacc,
                Guarantor.is_deleted == False))).scalar_one_or_none()  # noqa: E712
        if row is None:
            row = (await db.execute(select(Guarantor).where(
                Guarantor.account_no == acc, Guarantor.guarantor_name == gname,
                Guarantor.is_deleted == False))).scalar_one_or_none()  # noqa: E712
        if row is None:
            import uuid
            from datetime import datetime
            row = Guarantor(id=f"G-{acc}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:2]}",
                            account_no=acc, date_added=date.today().isoformat(), created_by=username)
            db.add(row)
            g_added += 1
        else:
            g_updated += 1
        row.guarantor_name = gname[:200]
        if gacc:
            row.guarantor_account = gacc[:50]
        if g.get("branch"):
            row.branch = str(g["branch"])[:20]
        if customer is not None and customer.name and not row.customer_name:
            row.customer_name = customer.name

    # Properties (املاک) — upsert with smart matching so a similar property isn't
    # duplicated: match on plate no / mortgage deed no, else type+address.
    p_added = p_updated = 0
    for p in (cust.get("properties") or []):
        if not isinstance(p, dict):
            continue
        ptype = (p.get("prop_type") or "").strip()
        addr = (p.get("address") or "").strip()
        plate = (p.get("plate_no") or "").strip()
        deed = (p.get("mortgage_deed_no") or "").strip()
        if not (ptype or addr or plate or deed):
            continue
        prow = await _match_property(db, acc, plate, deed, ptype, addr)
        if prow is None:
            import uuid
            from datetime import datetime
            prow = MortgagedProperty(id=f"PROP-{acc}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:2]}",
                                     account_no=acc, date_added=date.today().isoformat(), created_by=username)
            db.add(prow)
            p_added += 1
        else:
            p_updated += 1
        # fill-empty so curated values are never clobbered
        _set_prop(prow, "prop_type", ptype)
        _set_prop(prow, "address", addr)
        _set_prop(prow, "city", p.get("city"))
        _set_prop(prow, "country", p.get("country"))
        _set_prop(prow, "plate_no", plate)
        _set_prop(prow, "mortgage_deed_no", deed)
        _set_prop(prow, "mortgage_date", p.get("mortgage_date"))
        _set_prop(prow, "insurance_expiry", p.get("insurance_expiry"))
        _set_prop(prow, "valuation_currency", p.get("valuation_currency"))
        _set_prop(prow, "mortgage_currency", p.get("mortgage_currency"))
        if prow.valuation in (None, "") and _num(p.get("valuation")) is not None:
            prow.valuation = _num(p.get("valuation"))
        if prow.mortgage_amount in (None, "") and _num(p.get("mortgage_amount")) is not None:
            prow.mortgage_amount = _num(p.get("mortgage_amount"))
        if customer is not None and customer.name and not prow.customer_name:
            prow.customer_name = customer.name

    return {"ok": True, "account_no": acc, "name": name or acc,
            "customer_id": (customer.id if customer is not None else None),
            "facility_hint": (cust.get("fields", {}).get("proposed_facility")
                              or (cust.get("review", {}) or {}).get("proposed_facility") or ""),
            "fields_saved": sorted(fields.keys()),
            "guarantors_added": g_added, "guarantors_updated": g_updated,
            "properties_added": p_added, "properties_updated": p_updated}


def _num(v):
    try:
        s = re.sub(r"[^\d.\-]", "", str(v or ""))
        return float(s) if s not in ("", "-", ".") else None
    except Exception:
        return None


def _set_prop(row, col: str, v) -> None:
    """Fill-empty a string column on a property row (don't clobber)."""
    v = (str(v).strip() if v not in (None, "") else "")
    if v and not (getattr(row, col, "") or "").strip():
        column = row.__table__.columns.get(col)
        ml = getattr(getattr(column, "type", None), "length", None)
        setattr(row, col, v[:ml] if ml else v)


async def _match_property(db: AsyncSession, acc: str, plate: str, deed: str, ptype: str, addr: str):
    """Find an existing property for ``acc`` matching plate/deed, else type+address."""
    from app.models.profile_entities import MortgagedProperty as MP
    rows = (await db.execute(select(MP).where(MP.account_no == acc, MP.is_deleted == False))).scalars().all()  # noqa: E712
    for r in rows:
        if plate and (r.plate_no or "").strip().lower() == plate.lower():
            return r
        if deed and (r.mortgage_deed_no or "").strip().lower() == deed.lower():
            return r
    if ptype and addr:
        for r in rows:
            if (r.prop_type or "").strip().lower() == ptype.lower() and (r.address or "").strip().lower() == addr.lower():
                return r
    return None


def record_documents_on_profile(data: dict, documents: list, drive_link: str, drive_id: str, filename: str, sha: str = "") -> dict:
    """Append the page→document map + Drive link to a profile data_json dict
    (deduped by content hash, falling back to drive id). Mutates and returns it."""
    if not isinstance(data, dict):
        data = {}
    docs = data.get("imported_documents")
    if not isinstance(docs, list):
        docs = []
    # Drop any prior entry for the SAME file (by content hash or Drive id) so a
    # re-import refreshes in place instead of duplicating.
    def _same(d):
        if not isinstance(d, dict):
            return False
        if sha and d.get("sha") == sha:
            return True
        return bool(drive_id) and d.get("drive_id") == drive_id
    docs = [d for d in docs if not _same(d)]
    docs.append({
        "filename": filename, "drive_id": drive_id, "drive_link": drive_link, "sha": sha,
        "pages": [d for d in (documents or []) if isinstance(d, dict)],
        "imported_at": date.today().isoformat(),
    })
    data["imported_documents"] = docs
    return data


# ---------------------------------------------------------------------------
# Spreadsheet / Office tables → text, so a big table spanning many accounts can
# be fed to the model (chunked) and every row routed to its customer.
# ---------------------------------------------------------------------------
def workbook_to_text(data: bytes, filename: str) -> str:
    """Flatten an Excel/CSV file to CSV-like text across ALL sheets."""
    name = (filename or "").lower()
    if name.endswith(".csv"):
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return data.decode(enc)
            except Exception:
                continue
        return data.decode("utf-8", "replace")
    out: list[str] = []
    if name.endswith((".xlsx", ".xlsm")):
        import io
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        try:
            for sh in wb.sheetnames:
                ws = wb[sh]
                out.append(f"## Sheet: {sh}")
                for row in ws.iter_rows(values_only=True):
                    cells = ["" if v is None else str(v) for v in row]
                    if any(c.strip() for c in cells):
                        out.append(",".join(cells))
        finally:
            wb.close()
    elif name.endswith(".xls"):
        import xlrd
        wb = xlrd.open_workbook(file_contents=data)
        for sh in wb.sheets():
            out.append(f"## Sheet: {sh.name}")
            for r in range(sh.nrows):
                cells = [str(sh.cell_value(r, c)) for c in range(sh.ncols)]
                if any(c.strip() for c in cells):
                    out.append(",".join(cells))
    return "\n".join(out)


def chunk_text(text: str, max_chars: int = 100000) -> list[str]:
    """Split table text into chunks under ``max_chars``, repeating the sheet/header
    hint at the top of each chunk so every chunk stays self-describing."""
    lines = (text or "").split("\n")
    header = "\n".join(lines[:2])
    chunks: list[str] = []
    cur: list[str] = []
    size = 0
    for ln in lines:
        if size + len(ln) + 1 > max_chars and cur:
            chunks.append("\n".join(cur))
            cur = [header] if header else []
            size = len(header)
        cur.append(ln)
        size += len(ln) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks or [text]


def merge_customer(into: dict, more: dict) -> None:
    """Merge a customer dict parsed from a later chunk into an existing one."""
    for k, v in more.items():
        if k in ("fields", "review") and isinstance(v, dict):
            base = into.setdefault(k, {})
            for kk, vv in v.items():
                if vv not in (None, "") and not base.get(kk):
                    base[kk] = vv
        elif k == "guarantors" and isinstance(v, list):
            into.setdefault("guarantors", [])
            seen = {(g.get("name"), g.get("account")) for g in into["guarantors"] if isinstance(g, dict)}
            for g in v:
                if isinstance(g, dict) and (g.get("name"), g.get("account")) not in seen:
                    into["guarantors"].append(g)
        elif v not in (None, "") and not into.get(k):
            into[k] = v


# ---------------------------------------------------------------------------
# Oversized PDFs → split into page-chunks (each under the provider's inline
# limit) so a big file is extracted section-by-section and merged.
# ---------------------------------------------------------------------------
def split_pdf(data: bytes, max_bytes: int = 18 * 1024 * 1024, max_pages: int = 12):
    """Return ([(start_page_1based, pdf_bytes), ...], total_pages). Each chunk is
    <= max_bytes (or a single page if one page alone exceeds it)."""
    import io
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(data))
    n = len(reader.pages)
    chunks: list[tuple[int, bytes]] = []
    i = 0
    while i < n:
        end = min(i + max_pages, n)
        while end > i:
            w = PdfWriter()
            for p in range(i, end):
                w.add_page(reader.pages[p])
            buf = io.BytesIO()
            w.write(buf)
            b = buf.getvalue()
            if len(b) <= max_bytes or (end - i) == 1:
                chunks.append((i + 1, b))
                i = end
                break
            end -= 1
    return chunks, n


def offset_pages(pages: str, offset: int) -> str:
    """Shift the page numbers in a "1-2" / "3" string by ``offset`` (chunk → global)."""
    if not offset:
        return str(pages or "")
    return re.sub(r"\d+", lambda m: str(int(m.group()) + offset), str(pages or ""))
