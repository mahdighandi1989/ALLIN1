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
        "business_type": "", "trade_license_no": "", "trade_license_expiry": "",
        "established_since": "", "relationship_date": "", "aecb_score": "",
        "monthly_salary": "", "auditor": "", "address": "", "po_box": "",
        "passport_no": "", "passport_expiry": "", "emirates_id_no": "", "emirates_id_expiry": "",
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
    _apply_profile_scalars(cp, fields)  # promote known scalars to real columns
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


def record_documents_on_profile(data: dict, documents: list, drive_link: str, drive_id: str, filename: str) -> dict:
    """Append the page→document map + Drive link to a profile data_json dict
    (deduped by drive id). Mutates and returns ``data``."""
    if not isinstance(data, dict):
        data = {}
    docs = data.get("imported_documents")
    if not isinstance(docs, list):
        docs = []
    # Drop any prior entry for the same Drive file (re-import overwrites).
    docs = [d for d in docs if isinstance(d, dict) and d.get("drive_id") != drive_id]
    docs.append({
        "filename": filename, "drive_id": drive_id, "drive_link": drive_link,
        "pages": [d for d in (documents or []) if isinstance(d, dict)],
        "imported_at": date.today().isoformat(),
    })
    data["imported_documents"] = docs
    return data
