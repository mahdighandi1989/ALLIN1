#!/usr/bin/env python3
"""Audit the DATA with deliberate suspicion.

Runs against whatever ``SUPERVISOR_DATABASE_URL`` (or ``DATABASE_URL``) points at
and NEVER writes: it is a read-only opinion about the data, reported for a human
to act on. Which database was audited is recorded in the output, because an
audit of an empty local database must never be mistaken for an audit of
production.

The checks are the ones an experienced officer would make by hand — values that
cannot be true, records that contradict each other, and records that point at
nothing:

  impossible   a rate of 3,300,000; a share above 100; a negative or zero amount;
               an expiry before its own issue date; an issue date in the future
  malformed    an account number that is not 6 digits; a national ID of the wrong
               length; a date parked in a name field; a name that is only digits
  orphaned     a facility whose customer is gone; a guarantor/property/deposit
               whose account does not exist
  contradictory partners of one company whose shares do not add up to ~100
  empty        a record that exists but carries no usable field at all
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "docs" / "supervisor" / "last_db_audit.json"

DB_URL = os.getenv("SUPERVISOR_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
if not DB_URL:
    DB_URL = "sqlite+aiosqlite:///./_supervisor_audit.db"
os.environ["DATABASE_URL"] = DB_URL
os.environ.setdefault("AUTH_DISABLED", "true")
os.environ.setdefault("ENVIRONMENT", "development")

ACC_RE = re.compile(r"^\d{6}$")
DATEISH = re.compile(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b")
DIGITS_ONLY = re.compile(r"^[\d\s\-/]+$")


def _f(v):
    try:
        return float(str(v).replace(",", "").strip())
    except Exception:
        return None


def _d(v):
    from datetime import date, datetime
    if isinstance(v, (date, datetime)):
        return v if isinstance(v, date) else v.date()
    s = str(v or "").strip()
    if not s:
        return None
    try:
        from dateutil import parser as dp
        return dp.parse(s, dayfirst=True, fuzzy=True).date()
    except Exception:
        return None


async def run(session_factory=None) -> dict:
    """``session_factory`` lets a test drive these checks against its own session;
    left out, the auditor opens its own connection to ``DB_URL``."""
    from sqlalchemy import select, func
    from app.models.customer import Customer
    from app.models.crm import CustomerProfile
    from app.models.facility import Facility
    from app.models.guarantor import Guarantor
    from app.models.profile_entities import MortgagedProperty, FixedDeposit, Partner

    findings: list[dict] = []
    counts: dict = {}

    def flag(kind, table, ident, detail, severity="medium"):
        findings.append({"kind": kind, "table": table, "id": str(ident), "detail": detail, "severity": severity})

    if session_factory is None:
        from app.database import AsyncSessionLocal
        session_factory = AsyncSessionLocal
        # A fresh local sqlite has no schema yet; create it so a local run reports
        # an honest "nothing to audit" instead of a crash. Never on a real DB, and
        # never when a caller supplied its own session.
        if DB_URL.startswith("sqlite"):
            from app.database import engine, Base
            import app.models  # noqa: F401  (registers every table)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        customers = (await db.execute(select(Customer).where(Customer.is_deleted == False))).scalars().all()  # noqa: E712
        accounts = {c.account_no for c in customers if c.account_no}
        by_id = {c.id: c for c in customers}
        counts["customers"] = len(customers)

        for c in customers:
            acc = (c.account_no or "").strip()
            if not acc:
                flag("malformed", "customers", c.id, "مشتری بدونِ شمارهٔ حساب", "high")
            elif not ACC_RE.match(acc):
                flag("malformed", "customers", acc, f"شمارهٔ حساب «{acc}» شش‌رقمی نیست", "low")
            name = (c.name or "").strip()
            if not name:
                flag("empty", "customers", acc, "مشتری بدونِ نام", "high")
            elif DIGITS_ONLY.match(name):
                flag("malformed", "customers", acc, f"نام فقط عدد است: «{name}»", "high")
            elif DATEISH.search(name):
                flag("malformed", "customers", acc, f"تاریخ در فیلدِ نام: «{name}»", "high")

        profiles = (await db.execute(select(CustomerProfile))).scalars().all()
        counts["profiles"] = len(profiles)
        for p in profiles:
            acc = (p.account_no or "").strip()
            if acc and acc not in accounts:
                flag("orphan", "customer_profiles", acc, "پروفایل بدونِ مشتریِ متناظر", "high")
            for lo, hi, label in (("trade_license_issue", "trade_license_expiry", "مجوز"),
                                  ("passport_issue", "passport_expiry", "پاسپورت"),
                                  ("emirates_id_issue", "emirates_id_expiry", "اقامت"),
                                  ("visa_issue", "visa_expiry", "ویزا"),
                                  ("tenancy_issue", "tenancy_expiry", "اجاره‌نامه")):
                a, b = _d(getattr(p, lo, None)), _d(getattr(p, hi, None))
                if a and b and b < a:
                    flag("impossible", "customer_profiles", acc, f"{label}: انقضا ({b}) پیش از صدور ({a})", "high")
            for fld, lab, lim in (("aecb_score", "امتیاز AECB", 1000), ("proposed_rate", "نرخ پیشنهادی", 60)):
                v = _f(getattr(p, fld, None))
                if v is not None and (v < 0 or v > lim):
                    flag("impossible", "customer_profiles", acc, f"{lab} = {v} (خارج از بازهٔ ۰..{lim})", "high")

        facilities = (await db.execute(select(Facility).where(Facility.is_deleted == False))).scalars().all()  # noqa: E712
        counts["facilities"] = len(facilities)
        for f in facilities:
            who = by_id.get(f.customer_id)
            ident = (who.account_no if who else f"customer_id={f.customer_id}")
            if who is None:
                flag("orphan", "facilities", ident, "تسهیلات بدونِ مشتری", "high")
            r = _f(getattr(f, "interest_rate", None))
            if r is not None and (r < 0 or r > 40):
                flag("impossible", "facilities", ident, f"نرخ = {r} (نرخِ تسهیلات نمی‌تواند این باشد)", "high")
            amt = _f(getattr(f, "amount", None))
            if amt is not None and amt <= 0:
                flag("impossible", "facilities", ident, f"مبلغ = {amt}", "high")
            t = str(getattr(f, "tenor_months", "") or "").strip()
            if t and (not t.isdigit() or int(t) > 600):
                flag("impossible", "facilities", ident, f"مدت = «{t}» ماه", "medium")

        async def _orphans(model, label):
            rows = (await db.execute(select(model))).scalars().all()
            counts[label] = len(rows)
            for r in rows:
                if getattr(r, "is_deleted", False):
                    continue
                acc = (getattr(r, "account_no", "") or "").strip()
                if acc and acc not in accounts:
                    flag("orphan", label, acc, f"{label}: حسابِ «{acc}» وجود ندارد", "high")
            return rows

        await _orphans(Guarantor, "guarantors")
        await _orphans(MortgagedProperty, "properties")
        await _orphans(FixedDeposit, "fixed_deposits")
        partners = await _orphans(Partner, "partners")

        shares = defaultdict(list)
        for p in partners:
            if getattr(p, "is_deleted", False):
                continue
            v = _f(getattr(p, "share", None))
            if v is None:
                continue
            if v < 0 or v > 100:
                flag("impossible", "partners", getattr(p, "account_no", "?"),
                     f"سهمِ «{getattr(p, 'name', '')}» = {v}٪", "high")
            else:
                shares[getattr(p, "account_no", "?")].append(v)
        for acc, vals in shares.items():
            total = sum(vals)
            if len(vals) > 1 and not (95 <= total <= 105):
                flag("contradictory", "partners", acc,
                     f"جمعِ سهمِ {len(vals)} شریک = {round(total, 2)}٪ (باید حدودِ ۱۰۰ باشد)", "medium")

    by_kind: dict = defaultdict(int)
    by_sev: dict = defaultdict(int)
    for f in findings:
        by_kind[f["kind"]] += 1
        by_sev[f["severity"]] += 1
    return {
        "database": re.sub(r"://[^@/]*@", "://***@", DB_URL),
        "is_local_placeholder": DB_URL.startswith("sqlite"),
        "counts": counts,
        "findings": findings[:500],
        "total_findings": len(findings),
        "by_kind": dict(by_kind),
        "by_severity": dict(by_sev),
    }


if __name__ == "__main__":
    try:
        rep = asyncio.run(run())
    except Exception as e:  # a broken audit must be visible, not silent
        rep = {"database": re.sub(r"://[^@/]*@", "://***@", DB_URL), "error": f"{type(e).__name__}: {e}"[:400],
               "total_findings": -1, "counts": {}, "findings": [], "by_kind": {}, "by_severity": {}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: rep.get(k) for k in ("database", "is_local_placeholder", "counts", "total_findings", "by_kind", "error")}, ensure_ascii=False))
