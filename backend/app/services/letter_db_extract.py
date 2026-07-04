"""Persist AI-extracted letter facts into the RIGHT customer profile(s).

Two phases, both careful and conservative (the letter can name several customers,
and this writes to the production customer DB):

* :func:`stage_db_writes` — read-only. Resolve each proposed fact to a target
  account (account cited in the letter, else the primary customer, else a
  name-match; otherwise it stays UNRESOLVED and is surfaced as a note, never
  guessed), then decide **add / update / skip** against the live profile with a
  date-staleness guard. The user reviews these before anything is written.

* :func:`apply_db_writes` — writes only the items the user ticked. It re-checks
  dedup + staleness at write time (the profile may have moved since staging),
  creates the customer + profile when missing, mirrors a safe subset of keys to
  structured columns, and audits **every** write against the account so it shows
  in both the global activity log and that customer's profile «Logs» tab.

Nothing here deletes; nothing overwrites a newer dated value with an older one.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import CustomerProfile
from app.models.customer import Customer

logger = logging.getLogger(__name__)

# data_json keys that ALSO mirror to a structured CustomerProfile column.
KEY_TO_COLUMN = {
    "business_type": "business_type",
    "trade_license_no": "trade_license_no",
    "trade_license_expiry": "trade_license_expiry",
    "passport_no": "passport_no",
    "passport_expiry": "passport_expiry",
    "emirates_id_no": "emirates_id_no",
    "emirates_id_expiry": "emirates_id_expiry",
}


def _is_date_key(key: str) -> bool:
    k = (key or "").lower()
    return k.endswith(("_expiry", "_issue", "_date")) or k in ("date_of_birth", "dob")


def _newer(new: str, old: str) -> bool:
    """True if ``new`` is a strictly-or-equally later date than ``old`` (so we may
    replace). Unparseable ``new`` ⇒ False (keep old); unparseable ``old`` ⇒ True."""
    from app.services.doc_ingest import _newer_or_empty
    return _newer_or_empty(new, old)


def _norm_name(s: str) -> str:
    return " ".join((s or "").split()).lower()


def _profile_data(profile: Optional[CustomerProfile]) -> Dict[str, Any]:
    if profile is None or not getattr(profile, "data_json", None):
        return {}
    try:
        d = json.loads(profile.data_json)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _decide(existing: Any, value: str, key: str) -> str:
    """add | skip_same | skip_stale | update — the conservative resolution."""
    ex = ("" if existing is None else str(existing)).strip()
    if ex in ("", "-"):
        return "add"
    if ex == value.strip():
        return "skip_same"
    if _is_date_key(key) and not _newer(value, ex):
        return "skip_stale"
    return "update"


async def _find_by_account(db: AsyncSession, acc: str) -> Optional[Customer]:
    if not acc:
        return None
    return (
        await db.execute(
            sa.select(Customer).where(Customer.account_no == acc, Customer.is_deleted == False)  # noqa: E712
        )
    ).scalar_one_or_none()


async def _find_by_name(db: AsyncSession, name: str) -> Optional[Customer]:
    """Exact (case-insensitive) name match — only when UNambiguous (one row)."""
    n = _norm_name(name)
    if not n:
        return None
    rows = (
        await db.execute(
            sa.select(Customer).where(Customer.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    matches = [c for c in rows if _norm_name(c.name or "") == n]
    return matches[0] if len(matches) == 1 else None


async def stage_db_writes(
    db: AsyncSession, primary_account: str, primary_name: str,
    raw_writes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Resolve + classify each proposed fact against the live DB (read-only).

    Returns reviewable items: applicable ``db_write`` proposals (add/update) plus
    ``note`` items for the ones we deliberately won't auto-apply (unresolved
    customer, or already-present). Never writes."""
    out: List[Dict[str, Any]] = []
    # cache profile data per resolved account within this pass
    prof_cache: Dict[str, Dict[str, Any]] = {}

    async def prof_data(acc: str) -> Dict[str, Any]:
        if acc not in prof_cache:
            p = (await db.execute(
                sa.select(CustomerProfile).where(CustomerProfile.account_no == acc)
            )).scalar_one_or_none()
            prof_cache[acc] = _profile_data(p)
        return prof_cache[acc]

    for i, w in enumerate(raw_writes):
        key, value = w["key"], w["value"]
        acc = (w.get("account_no") or "").strip()
        name = (w.get("customer_name") or "").strip()

        target: Optional[str] = None
        target_name = name or primary_name
        exists = True
        resolution = ""
        if acc:
            cust = await _find_by_account(db, acc)
            target, resolution, exists = acc, "account_cited", (cust is not None)
            if cust and not name:
                target_name = cust.name or name
        elif name and primary_name and _norm_name(name) == _norm_name(primary_name):
            target, resolution = primary_account, "primary"
        elif name:
            cust = await _find_by_name(db, name)
            if cust:
                target, resolution, target_name = cust.account_no, "matched_name", cust.name or name
            else:
                # can't key a profile without an account → surface, don't guess
                out.append({
                    "id": f"d{i}", "op": "note", "category": "db_extract", "field": key, "key": key,
                    "title": f"مشتری «{name}» شناسایی نشد",
                    "detail": f"«{key} = {value}» — این مشتری در پایگاه‌داده نیست و شماره‌حساب در نامه ذکر نشده؛ برای ثبت، شماره‌حساب لازم است.",
                    "severity": "medium", "applicable": False,
                })
                continue
        else:
            target, resolution = primary_account, "primary_default"

        if not target:
            continue
        data = await prof_data(target)
        action = _decide(data.get(key), value, key)
        if action in ("skip_same", "skip_stale"):
            out.append({
                "id": f"d{i}", "op": "note", "category": "db_extract", "field": key, "key": key,
                "title": ("از قبل ثبت شده: " if action == "skip_same" else "نسخهٔ پایگاه‌داده به‌روزتر است: ") + key,
                "detail": f"مشتری {target_name} ({target}) — «{key}»: مقدارِ نامه «{value}»، مقدارِ فعلی «{data.get(key)}».",
                "severity": "low", "applicable": False,
            })
            continue

        out.append({
            "id": f"d{i}", "op": "db_write", "category": "db_extract", "field": key,
            "account_no": target, "customer_name": target_name, "key": key, "value": value,
            "action": action, "before": ("" if action == "add" else str(data.get(key) or "")),
            "after": value, "resolution": resolution, "exists": exists,
            "title": w.get("title") or (f"{'ثبتِ' if action == 'add' else 'به‌روزرسانیِ'} «{key}» برای {target_name}"),
            "detail": w.get("detail") or "",
            "severity": "medium", "applicable": True,
        })
    return out


async def apply_db_writes(
    db: AsyncSession, user, request, items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Persist the ticked facts. Re-checks dedup/staleness, creates the customer +
    profile when missing, mirrors safe keys to columns, audits each write to the
    account. Commits once. Returns per-item outcomes + counts."""
    from app.services.customer_link import ensure_customer
    from app.services.audit import record_audit
    from datetime import date

    outcomes: List[Dict[str, Any]] = []
    counts = {"added": 0, "updated": 0, "skipped": 0, "profiles_created": 0}
    audit_calls: List[Dict[str, Any]] = []
    # Batch caches: several facts can target the SAME (possibly brand-new) account,
    # and none are flushed until the final commit — so re-querying would miss the
    # in-memory rows and create UNIQUE-violating duplicates. Reuse per account.
    ensured: set = set()
    profiles: Dict[str, CustomerProfile] = {}
    created_accounts: set = set()

    for it in items:
        acc = (it.get("account_no") or "").strip()
        key = str(it.get("key") or "").strip()
        value = str(it.get("value") or "").strip()
        name = (it.get("customer_name") or "").strip()
        if not acc or not key or not value:
            outcomes.append({"account_no": acc, "key": key, "outcome": "invalid"})
            continue

        # ensure the Customer row exists (create a stub if this account is new) —
        # once per account per batch (ensure_customer doesn't flush).
        if acc not in ensured:
            await ensure_customer(db, acc, name or None)
            ensured.add(acc)

        profile = profiles.get(acc)
        if profile is None:
            profile = (await db.execute(
                sa.select(CustomerProfile).where(CustomerProfile.account_no == acc)
            )).scalar_one_or_none()
            if profile is None:
                profile = CustomerProfile(account_no=acc, customer_name=name or acc)
                db.add(profile)
                created_accounts.add(acc)
            profiles[acc] = profile
        profile_created = acc in created_accounts

        data = _profile_data(profile)
        action = _decide(data.get(key), value, key)
        if action in ("skip_same", "skip_stale"):
            counts["skipped"] += 1
            outcomes.append({"account_no": acc, "key": key, "outcome": "skipped", "reason": action})
            continue

        data[key] = value
        profile.data_json = json.dumps(data, ensure_ascii=False)
        col = KEY_TO_COLUMN.get(key)
        if col is not None and hasattr(profile, col):
            cur = (getattr(profile, col) or "").strip()
            if not cur or not _is_date_key(key) or _newer(value, cur):
                setattr(profile, col, value[:80])
        if name and not (profile.customer_name or "").strip():
            profile.customer_name = name[:200]
        profile.last_updated = date.today().isoformat()
        profile.updated_by = getattr(user, "username", "") or ""

        if action == "add":
            counts["added"] += 1
        else:
            counts["updated"] += 1
        outcomes.append({
            "account_no": acc, "key": key, "outcome": ("added" if action == "add" else "updated"),
            "profile_created": profile_created,
        })
        audit_calls.append({
            "action": "create" if action == "add" else "update",
            "account_no": acc, "key": key, "value": value, "was_new_profile": profile_created,
        })

    counts["profiles_created"] = len(created_accounts)
    await db.commit()

    # Audit AFTER the commit so each entry reflects a persisted change (and a failed
    # write never leaves a phantom log line). account_no ties it to the profile tab.
    for a in audit_calls:
        detail = (f"ثبتِ دادهٔ استخراج‌شده از نامه: «{a['key']}» = «{a['value']}»"
                  + (" (پروفایلِ جدید ساخته شد)" if a["was_new_profile"] else ""))
        await record_audit(
            action=a["action"], entity_type="profile_extract", entity_id=a["key"],
            account_no=a["account_no"], detail=detail, user=user, request=request, db=db,
        )

    return {"ok": True, "outcomes": outcomes, "counts": counts}
