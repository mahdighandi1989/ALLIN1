"""Profile completeness — what a customer's record is actually missing.

The Excel system computed this (ProfileGetCompleteness / ShowMissingFields) so the
KYC and Summary wizards only asked for what was absent (requirements A1 / A25).

v130 — the field list is no longer a hand-written shortlist. Until now this scored
**13 items** (10 profile fields + 3 "does a related record exist" checks), so a
customer could read **100%** while most of the record the Credit File Summary form
needs was empty — which is exactly why gaps were only discovered while filling that
form by hand. The score now covers EVERY field the Summary forms read, split into
sections, and is ACCOUNT-TYPE AWARE: a retail customer is not marked down for a
trade licence it can never have, and a corporate one is not let off for missing it.

The same spec drives (a) this score, (b) the per-section "what is missing" list the
UI shows, and (c) the post-import gap report — so the three can never drift apart.
"""
from __future__ import annotations

from sqlalchemy import select, func

from app.models.crm import CustomerProfile
from app.models.customer import Customer
from app.models.facility import Facility
from app.models.guarantor import Guarantor
from app.models.security import Security
from app.models.profile_entities import MortgagedProperty, FixedDeposit

CORP = "corporate"
RETAIL = "retail"
BOTH = (CORP, RETAIL)

# (section_key, attribute, Persian label, which account types need it)
# Every entry is read by the Credit File Summary form (corporate and/or retail),
# by the Offer Letter, or by the KYC expiry watcher.
# NOT included on purpose: the `*_remarks` columns. Those are the OFFICER'S own
# notes — a document never states them — so an empty one is not a data gap and
# counting it would depress every score with noise.
_FIELD_SPECS: list[tuple[str, str, str, tuple[str, ...]]] = [
    # --- identity / base -----------------------------------------------------
    ("identity", "business_type", "نوع فعالیت", (CORP,)),
    # the model calls this "nationality"; the column is passport_nationality
    ("identity", "passport_nationality", "تابعیت", BOTH),
    ("identity", "national_id", "کد ملی / شناسه", BOTH),
    ("identity", "established_since", "تاریخ تأسیس", (CORP,)),
    ("identity", "relationship_date", "تاریخ شروع رابطه", BOTH),
    ("identity", "auditor", "حسابرس", (CORP,)),
    # --- KYC documents -------------------------------------------------------
    ("kyc", "trade_license_no", "شمارهٔ مجوز تجاری", (CORP,)),
    ("kyc", "trade_license_issue", "تاریخ صدور مجوز", (CORP,)),
    ("kyc", "trade_license_expiry", "تاریخ انقضای مجوز", (CORP,)),
    ("kyc", "passport_no", "شمارهٔ پاسپورت", BOTH),
    ("kyc", "passport_issue", "تاریخ صدور پاسپورت", BOTH),
    ("kyc", "passport_expiry", "تاریخ انقضای پاسپورت", BOTH),
    ("kyc", "emirates_id_no", "شمارهٔ اقامت (EID)", BOTH),
    ("kyc", "emirates_id_issue", "تاریخ صدور اقامت", BOTH),
    ("kyc", "emirates_id_expiry", "تاریخ انقضای اقامت", BOTH),
    ("kyc", "emirates_id_golden", "اقامتِ طلایی (بله/خیر)", BOTH),
    ("kyc", "visa_no", "شمارهٔ ویزا", BOTH),
    ("kyc", "visa_issue", "تاریخ صدور ویزا", BOTH),
    ("kyc", "visa_expiry", "تاریخ انقضای ویزا", BOTH),
    ("kyc", "visa_type", "نوع ویزا", BOTH),
    ("kyc", "tenancy_no", "شمارهٔ اجاره‌نامه", (CORP,)),
    ("kyc", "tenancy_issue", "تاریخ صدور اجاره‌نامه", (CORP,)),
    ("kyc", "tenancy_expiry", "تاریخ انقضای اجاره‌نامه", (CORP,)),
    ("kyc", "tenancy_address", "نشانیِ اجاره‌نامه", (CORP,)),
    # --- credit / review -----------------------------------------------------
    ("credit", "rating", "ریتینگ", BOTH),
    ("credit", "grade", "گرید (سابقه)", BOTH),
    ("credit", "aecb_score", "امتیاز AECB", BOTH),
    ("credit", "monthly_salary", "حقوق ماهانه", (RETAIL,)),
    ("credit", "call_report", "Call Report", BOTH),
    ("credit", "previous_files", "تعداد پرونده‌های قبلی", BOTH),
    ("credit", "undertaking_from", "تعهدنامه از", BOTH),
    ("credit", "credit_application_no", "شمارهٔ درخواست اعتباری", BOTH),
    ("credit", "review_date", "تاریخ بازبینی", BOTH),
    ("credit", "proposed_facility", "تسهیلات پیشنهادی", BOTH),
    ("credit", "proposed_amount", "مبلغ پیشنهادی", BOTH),
    ("credit", "proposed_tenor", "مدت پیشنهادی", BOTH),
    ("credit", "proposed_rate", "نرخ پیشنهادی", BOTH),
]

SECTION_TITLES = {
    "identity": "هویت و پایه",
    "kyc": "مدارک و KYC",
    "credit": "اعتباری و بازبینی",
    "records": "رکوردهای مرتبط",
}
SECTION_ORDER = ["identity", "kyc", "credit", "records"]


def normalize_account_type(value) -> str:
    """'corporate' unless the record explicitly says retail — the corporate set is
    the wider one, so an unknown type is scored strictly rather than leniently."""
    v = str(getattr(value, "value", value) or "").strip().lower()
    return RETAIL if v == RETAIL else CORP


def field_specs_for(account_type: str) -> list[tuple[str, str, str]]:
    """(section, attribute, label) for the fields THIS account type needs."""
    at = normalize_account_type(account_type)
    return [(s, a, lbl) for s, a, lbl, types in _FIELD_SPECS if at in types]


def _filled(value) -> bool:
    return bool(str(value).strip()) if value is not None else False


def build_report(account_no: str, account_type, profile, counts: dict) -> dict:
    """Pure scoring — no DB access, so it serves both the per-customer endpoint and
    the bulk data-quality sweep from one code path.

    ``counts`` holds the related-record tallies:
    facilities / guarantors / securities / properties / deposits / partners.
    """
    at = normalize_account_type(account_type)
    sections: dict[str, dict] = {
        k: {"key": k, "title": SECTION_TITLES[k], "filled": 0, "total": 0, "missing": []}
        for k in SECTION_ORDER
    }

    for sec, attr, label in field_specs_for(at):
        s = sections[sec]
        s["total"] += 1
        if _filled(getattr(profile, attr, None) if profile is not None else None):
            s["filled"] += 1
        else:
            s["missing"].append({"field": attr, "label": label})

    # Related records: presence checks, same shape so the UI treats them alike.
    rec_items = [
        ("facilities", "حداقل یک تسهیلات", (counts.get("facilities") or 0) > 0),
        ("guarantee", "ضامن یا چکِ تضمینی",
         (counts.get("guarantors") or 0) > 0 or (counts.get("securities") or 0) > 0),
        ("collateral", "وثیقه (ملک یا سپرده)",
         (counts.get("properties") or 0) > 0 or (counts.get("deposits") or 0) > 0),
    ]
    if at == CORP:
        rec_items.append(("partners", "شرکا / مدیران", (counts.get("partners") or 0) > 0))
    rec = sections["records"]
    for field, label, ok in rec_items:
        rec["total"] += 1
        if ok:
            rec["filled"] += 1
        else:
            rec["missing"].append({"field": field, "label": label})

    for s in sections.values():
        s["percent"] = round(100 * s["filled"] / s["total"]) if s["total"] else 100

    filled = sum(s["filled"] for s in sections.values())
    total = sum(s["total"] for s in sections.values())
    percent = round(100 * filled / total) if total else 0
    ordered = [sections[k] for k in SECTION_ORDER if sections[k]["total"]]

    return {
        "account_no": account_no,
        "account_type": at,
        "percent": percent,
        "filled": filled,
        "total": total,
        # back-compat: the old flat list of human-readable labels
        "missing": [m["label"] for s in ordered for m in s["missing"]],
        "sections": ordered,
    }


async def gather_counts(db, account_no: str) -> dict:
    """Related-record tallies for ONE account."""
    acc = (account_no or "").strip()

    async def _count(model) -> int:
        q = select(func.count()).select_from(model).where(model.account_no == acc)
        if hasattr(model, "is_deleted"):
            q = q.where(model.is_deleted == False)  # noqa: E712
        return (await db.execute(q)).scalar() or 0

    cid = (await db.execute(select(Customer.id).where(Customer.account_no == acc))).scalar_one_or_none()
    fac = 0
    if cid:
        fac = (await db.execute(
            select(func.count()).select_from(Facility).where(
                Facility.customer_id == cid, Facility.is_deleted == False)  # noqa: E712
        )).scalar() or 0

    partners = 0
    try:  # partners live on their own table when the schema has it
        from app.models.profile_entities import Partner
        partners = await _count(Partner)
    except Exception:  # pragma: no cover - older schema without the table
        partners = 0

    return {
        "facilities": fac,
        "guarantors": await _count(Guarantor),
        "securities": await _count(Security),
        "properties": await _count(MortgagedProperty),
        "deposits": await _count(FixedDeposit),
        "partners": partners,
    }


async def recompute_completeness(db, account_no: str) -> dict:
    """Recompute completeness for an account, persist the % on the profile, and
    return the full report. Caller commits."""
    acc = (account_no or "").strip()
    cp = (await db.execute(
        select(CustomerProfile).where(CustomerProfile.account_no == acc))).scalar_one_or_none()
    at = (await db.execute(
        select(Customer.account_type).where(Customer.account_no == acc))).scalar_one_or_none()
    if at is None and cp is not None:
        at = getattr(cp, "account_type", None)

    report = build_report(acc, at, cp, await gather_counts(db, acc))
    if cp is not None:
        cp.profile_completeness = f"{report['percent']}%"
    return report


async def sweep_all(db, *, limit: int = 2000) -> dict:
    """v130 — score EVERY customer in a handful of queries, not one per customer.

    The owner's problem was that gaps only surfaced one record at a time, while
    filling a form by hand. This answers the other question — "where is my data
    worst, and which field is missing most often across the book?" — cheaply
    enough to run on demand: 6 queries total regardless of how many customers
    exist, with the per-record scoring done in Python by :func:`build_report`.
    """
    rows = (await db.execute(
        select(Customer.account_no, Customer.name, Customer.account_type, Customer.branch)
        .where(Customer.is_deleted == False)  # noqa: E712
        .order_by(Customer.account_no).limit(limit))).all()
    accounts = [r[0] for r in rows if r[0]]
    if not accounts:
        return {"customers": [], "total_customers": 0, "average_percent": 0,
                "sections": [], "common_gaps": []}

    profiles = {
        p.account_no: p for p in (await db.execute(
            select(CustomerProfile).where(CustomerProfile.account_no.in_(accounts)))).scalars().all()
    }

    async def _tally(model, key: str) -> dict:
        q = (select(model.account_no, func.count())
             .where(model.account_no.in_(accounts)).group_by(model.account_no))
        if hasattr(model, "is_deleted"):
            q = q.where(model.is_deleted == False)  # noqa: E712
        return {a: n for a, n in (await db.execute(q)).all()}

    tallies = {
        "guarantors": await _tally(Guarantor, "guarantors"),
        "securities": await _tally(Security, "securities"),
        "properties": await _tally(MortgagedProperty, "properties"),
        "deposits": await _tally(FixedDeposit, "deposits"),
    }
    try:
        from app.models.profile_entities import Partner
        tallies["partners"] = await _tally(Partner, "partners")
    except Exception:  # pragma: no cover - older schema
        tallies["partners"] = {}

    # facilities hang off customer_id, so map id → account first
    id_to_acc = {
        cid: acc for cid, acc in (await db.execute(
            select(Customer.id, Customer.account_no)
            .where(Customer.account_no.in_(accounts)))).all()
    }
    fac_by_acc: dict = {}
    for cid, n in (await db.execute(
            select(Facility.customer_id, func.count())
            .where(Facility.customer_id.in_(list(id_to_acc.keys())),
                   Facility.is_deleted == False)  # noqa: E712
            .group_by(Facility.customer_id))).all():
        acc = id_to_acc.get(cid)
        if acc:
            fac_by_acc[acc] = fac_by_acc.get(acc, 0) + n

    out: list[dict] = []
    gap_counts: dict[str, dict] = {}
    sec_totals: dict[str, list[int]] = {k: [0, 0] for k in SECTION_ORDER}

    for acc, name, at, branch in rows:
        if not acc:
            continue
        counts = {k: tallies[k].get(acc, 0) for k in
                  ("guarantors", "securities", "properties", "deposits", "partners")}
        counts["facilities"] = fac_by_acc.get(acc, 0)
        rep = build_report(acc, at, profiles.get(acc), counts)
        for s in rep["sections"]:
            sec_totals[s["key"]][0] += s["filled"]
            sec_totals[s["key"]][1] += s["total"]
            for m in s["missing"]:
                g = gap_counts.setdefault(m["field"], {
                    "field": m["field"], "label": m["label"],
                    "section": s["key"], "section_title": s["title"], "count": 0})
                g["count"] += 1
        out.append({
            "account_no": acc, "name": name or "", "branch": branch or "",
            "account_type": rep["account_type"], "percent": rep["percent"],
            "filled": rep["filled"], "total": rep["total"],
            "missing_count": rep["total"] - rep["filled"],
            "sections": [{"key": s["key"], "percent": s["percent"],
                          "missing": len(s["missing"])} for s in rep["sections"]],
            "top_missing": [m["label"] for s in rep["sections"] for m in s["missing"]][:6],
        })

    out.sort(key=lambda x: (x["percent"], -x["missing_count"]))
    avg = round(sum(x["percent"] for x in out) / len(out)) if out else 0
    return {
        "customers": out,
        "total_customers": len(out),
        "average_percent": avg,
        "sections": [
            {"key": k, "title": SECTION_TITLES[k], "filled": sec_totals[k][0],
             "total": sec_totals[k][1],
             "percent": round(100 * sec_totals[k][0] / sec_totals[k][1]) if sec_totals[k][1] else 100}
            for k in SECTION_ORDER if sec_totals[k][1]
        ],
        "common_gaps": sorted(gap_counts.values(), key=lambda g: -g["count"]),
    }
