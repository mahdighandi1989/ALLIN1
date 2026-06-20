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
from app.services.customer_link import ensure_customer

EXTRACTION_PROMPT = """You are a meticulous UAE banking credit-file analyst. Read the ATTACHED document(s) end to end (every page) and extract the data for the bank's customer database.

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
        "business_type": "", "trade_license_no": "", "trade_license_issue": "", "trade_license_expiry": "",
        "established_since": "", "relationship_date": "", "aecb_score": "",
        "monthly_salary": "", "auditor": "", "address": "", "po_box": "",
        "passport_no": "", "passport_issue": "", "passport_expiry": "", "nationality": "",
        "emirates_id_no": "", "emirates_id_issue": "", "emirates_id_expiry": "",
        "visa_no": "", "visa_expiry": "", "tenancy_no": "", "tenancy_expiry": "",
        "proposed_facility": "", "proposed_amount": "", "proposed_tenor": "", "proposed_rate": ""
      },
      "guarantors": [ {"name": "", "account": "", "branch": ""} ],
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
- Only include fields you actually find; omit unknowns (do NOT invent values).
- Always capture the customer's full legal NAME exactly as printed.
- Capture each ID document's NUMBER together with its ISSUE and EXPIRY dates.
- "nationality" ONLY if it is explicitly printed — never guess or assume it.
- "account_no" is the 6-digit core (the middle group of 2624-115524-011 is 115524).
- Numbers as plain digits (no thousands separators) where possible.
- "documents" must list, for EVERY page or page-range, which document it is and which account it belongs to.
- Output ONLY the JSON object."""


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


async def persist_customer(db: AsyncSession, cust: dict, username: str, source: str = "import_ai") -> dict:
    """Apply one extracted customer dict to the DB (deduped). Returns a summary."""
    from app.routers.crm import _apply_profile_scalars, _upsert_credit_review  # shared helpers

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
    _apply_profile_scalars(cp, fields)  # promote known credit scalars to real columns
    # Promote identity/KYC facts to their real columns — fill-empty so the model
    # can never overwrite a value an officer already curated (e.g. a wrong
    # nationality won't clobber a correct one).
    _kyc_map = {
        "trade_license_no": "trade_license_no", "trade_license_issue": "trade_license_issue",
        "trade_license_expiry": "trade_license_expiry",
        "passport_no": "passport_no", "passport_issue": "passport_issue", "passport_expiry": "passport_expiry",
        "nationality": "passport_nationality", "passport_nationality": "passport_nationality",
        "emirates_id_no": "emirates_id_no", "emirates_id_issue": "emirates_id_issue", "emirates_id_expiry": "emirates_id_expiry",
        "visa_no": "visa_no", "visa_expiry": "visa_expiry",
        "tenancy_no": "tenancy_no", "tenancy_expiry": "tenancy_expiry",
    }
    for src, col in _kyc_map.items():
        v = fields.get(src)
        if not v:
            continue
        cur = (getattr(cp, col, "") or "").strip()
        # ID dates UPDATE on renewal (later date wins); numbers/nationality are
        # fill-empty (never clobbered by a possibly-wrong extraction).
        take = _newer_or_empty(str(v), cur) if col in _KYC_DATE_COLS else (not cur)
        if take:
            column = cp.__table__.columns.get(col)
            ml = getattr(getattr(column, "type", None), "length", None)
            setattr(cp, col, str(v)[:ml] if ml else str(v))
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

    return {"ok": True, "account_no": acc, "name": name or acc,
            "fields_saved": sorted(fields.keys()),
            "guarantors_added": g_added, "guarantors_updated": g_updated}


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
