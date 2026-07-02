"""Deterministic database cleanup / de-duplication — REVIEW FIRST.

Finds duplicate & contradictory per-customer child records (mortgaged properties,
fixed deposits, partners, guarantors) using the SAME matching primitives as the
AI import (``doc_ingest``) so import and cleanup always agree. It keeps the most
complete row of each duplicate set and soft-deletes the rest (reversible via the
Recycle Bin). Facilities & securities are REPORTED for manual review only — never
auto-removed (they're too important to touch automatically).

Flow:
  * ``scan(db)``  → a full report of what WOULD change. Changes nothing.
  * ``apply(db, user)`` → re-scans (deterministic) and soft-deletes the removals,
    logging every removal per-customer via ``record_audit`` (so it shows in that
    customer's «Logs» tab AND the global audit page). Returns a summary.

No AI is required for the core engine (safe, offline, predictable); an optional
AI «second opinion» can enrich the report separately (see ``ai_second_opinion``).
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.facility import Facility
from app.models.guarantor import Guarantor
from app.models.profile_entities import MortgagedProperty, FixedDeposit, Partner

# columns that are bookkeeping, not "data completeness"
_SKIP_COLS = {"id", "account_no", "is_deleted", "created_at", "created_by",
              "date_added", "facility_id", "customer_name"}


def _nz(v) -> bool:
    return v not in (None, "") and str(v).strip() != ""


def _data_cols(model) -> list[str]:
    return [c.name for c in model.__table__.columns if c.name not in _SKIP_COLS]


def _completeness(row, cols) -> int:
    return sum(1 for c in cols if _nz(getattr(row, c, None)))


def _age_key(row):
    """Sort helper: earliest first (oldest record is the 'original')."""
    return getattr(row, "created_at", None) or datetime.max.replace(tzinfo=None)


# ---- pairwise duplicate tests — CONSERVATIVE (safe for automatic deletion) ----
# Two records are the SAME only when they share a STRONG, unique identifier (the
# registered deed / plate / cheque no. / FD no.) AND no distinguishing field
# CONFLICTS (both populated but different). This is deliberately stricter than the
# fuzzy import matcher: two flats on the same building plan but with different
# deeds, two different security cheques from one guarantor, or two units of one
# deed with different valuations are DISTINCT and must never be merged/deleted.
def _eq(a, b) -> bool:
    a = (str(a).strip().lower() if a not in (None, "") else "")
    b = (str(b).strip().lower() if b not in (None, "") else "")
    return bool(a) and a == b


def _values_conflict(va, vb) -> bool:
    """True when both values are present but genuinely different (numeric-aware)."""
    if not (_nz(va) and _nz(vb)):
        return False
    try:
        return abs(float(va) - float(vb)) > 1e-9
    except (TypeError, ValueError):
        return str(va).strip().lower() != str(vb).strip().lower()


def _no_conflict(a, b, fields) -> bool:
    """True when NONE of ``fields`` conflicts between a and b."""
    return not any(_values_conflict(getattr(a, f, None), getattr(b, f, None)) for f in fields)


def _norm_name(s) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(s or "").lower())).strip()


# If any distinguishing field differs (both populated), the rows are NOT the same
# record, even when a strong id matches — this is what stops distinct-but-similar
# records (different deeds/units/cheques) from being wrongly merged.
_PROP_DISTINGUISH = ("mortgage_deed_no", "plate_no", "valuation", "mortgage_amount", "address")
_GUAR_DISTINGUISH = ("cheque_amount", "guarantor_name")
_FD_DISTINGUISH = ("amount", "maturity_date")
_PARTNER_DISTINGUISH = ("share",)


def _props_match(a, b) -> bool:
    strong = _eq(a.mortgage_deed_no, b.mortgage_deed_no) or _eq(a.plate_no, b.plate_no)
    return strong and _no_conflict(a, b, _PROP_DISTINGUISH)


def _guar_match(a, b) -> bool:
    return _eq(a.cheque_no, b.cheque_no) and _no_conflict(a, b, _GUAR_DISTINGUISH)


def _fd_match(a, b) -> bool:
    return _eq(a.fd_number, b.fd_number) and _no_conflict(a, b, _FD_DISTINGUISH)


def _partner_match(a, b) -> bool:
    na, nb = _norm_name(a.name), _norm_name(b.name)
    return bool(na) and na == nb and _no_conflict(a, b, _PARTNER_DISTINGUISH)


def _match_reason(a, b) -> str:
    """Short Persian explanation of WHY two rows are treated as the same record —
    surfaced in the report so a reviewer can trust (or challenge) each grouping."""
    if _eq(getattr(a, "mortgage_deed_no", None), getattr(b, "mortgage_deed_no", None)):
        return "سندِ رهنیِ یکسان"
    if _eq(getattr(a, "plate_no", None), getattr(b, "plate_no", None)):
        return "پلاکِ یکسان"
    if _eq(getattr(a, "cheque_no", None), getattr(b, "cheque_no", None)):
        return "شمارهٔ چکِ یکسان"
    if _eq(getattr(a, "fd_number", None), getattr(b, "fd_number", None)):
        return "شمارهٔ سپردهٔ یکسان"
    if _norm_name(getattr(a, "name", None)) and _norm_name(getattr(a, "name", None)) == _norm_name(getattr(b, "name", None)):
        return "نامِ کاملاً یکسان"
    return "شناسهٔ یکسان"


def _fac_match(a, b) -> bool:
    ta = str(getattr(a.facility_type, "value", a.facility_type) or "")
    tb = str(getattr(b.facility_type, "value", b.facility_type) or "")
    return bool(ta) and ta == tb and a.amount is not None and a.amount == b.amount


# ---- summaries for the report ----
def _prop_summary(r) -> str:
    bits = [r.prop_type, r.address, (f"پلاک {r.plate_no}" if _nz(r.plate_no) else ""),
            (f"سند {r.mortgage_deed_no}" if _nz(r.mortgage_deed_no) else ""),
            (f"ارزش {r.valuation}" if _nz(r.valuation) else "")]
    return " — ".join(x for x in (str(b).strip() for b in bits) if x) or "(بدون مشخصات)"


def _guar_summary(r) -> str:
    bits = [r.guarantor_name, (f"چک {r.cheque_no}" if _nz(r.cheque_no) else ""),
            (f"مبلغ {r.cheque_amount}" if _nz(r.cheque_amount) else ""), r.issuing_bank]
    return " — ".join(x for x in (str(b).strip() for b in bits) if x) or "(بدون مشخصات)"


def _fd_summary(r) -> str:
    bits = [(f"سپرده {r.fd_number}" if _nz(r.fd_number) else ""),
            (f"مبلغ {r.amount}" if _nz(r.amount) else ""),
            (f"سررسید {r.maturity_date}" if _nz(r.maturity_date) else "")]
    return " — ".join(x for x in (str(b).strip() for b in bits) if x) or "(بدون مشخصات)"


def _partner_summary(r) -> str:
    bits = [r.name, r.nationality, (f"سهم {r.share}" if _nz(r.share) else "")]
    return " — ".join(x for x in (str(b).strip() for b in bits) if x) or "(بدون مشخصات)"


def _fac_summary(r) -> str:
    ft = str(getattr(r.facility_type, "value", r.facility_type) or "")
    bits = [r.name, ft, (f"مبلغ {r.amount} {r.currency or ''}".strip() if _nz(r.amount) else "")]
    return " — ".join(x for x in (str(b).strip() for b in bits) if x) or "(بدون مشخصات)"


# entity → (model, account attribute, audit entity_type, Persian label, match fn, summary fn)
_ENTITIES = [
    ("properties", MortgagedProperty, "account_no", "property", "املاک مرهونه", _props_match, _prop_summary),
    ("guarantors", Guarantor, "account_no", "guarantor", "ضامن‌ها", _guar_match, _guar_summary),
    ("fixed_deposits", FixedDeposit, "account_no", "fixed_deposit", "سپرده‌های ثابت", _fd_match, _fd_summary),
    ("partners", Partner, "account_no", "partner", "شرکا", _partner_match, _partner_summary),
]


def _group_dupes(rows, match, cols):
    """Cluster ``rows`` (all same account) into duplicate sets. CONSERVATIVE: every
    removal must match the KEEPER directly — no transitive chains — so a near-match
    can never drag an unrelated record into a group and get it deleted. The keeper
    is the most complete row (tie: oldest), chosen first so it anchors the group."""
    n = len(rows)
    used = [False] * n
    # Most-complete (then oldest) first, so the best row becomes each group's keeper.
    order = sorted(range(n), key=lambda i: (-_completeness(rows[i], cols), _age_key(rows[i])))
    out = []
    for i in order:
        if used[i]:
            continue
        used[i] = True
        keeper = rows[i]
        removals = []
        for j in order:
            if used[j]:
                continue
            if match(keeper, rows[j]):   # must be a duplicate of the KEEPER itself
                used[j] = True
                removals.append(rows[j])
        if removals:
            out.append((keeper, removals))
    return out


def _conflict(keeper, removals, cols) -> list[str]:
    """Data columns where members disagree (both non-empty but different) — these
    duplicates carry contradictory data worth a human glance."""
    bad = []
    for c in cols:
        vals = {str(getattr(r, c)).strip() for r in [keeper, *removals] if _nz(getattr(r, c, None))}
        if len(vals) > 1:
            bad.append(c)
    return bad


async def scan(db: AsyncSession) -> dict:
    """Build the full de-dup report (changes NOTHING)."""
    # account_no → customer name (for the report)
    name_by_acc = dict((await db.execute(
        select(Customer.account_no, Customer.name).where(Customer.is_deleted == False))).all())  # noqa: E712

    groups: dict[str, list] = {}
    counts: dict[str, int] = {}
    total_removals = 0

    for key, model, acc_attr, _audit, label, match, summ in _ENTITIES:
        cols = _data_cols(model)
        rows = list((await db.execute(
            select(model).where(model.is_deleted == False))).scalars().all())  # noqa: E712
        by_acc: dict[str, list] = {}
        for r in rows:
            by_acc.setdefault((getattr(r, acc_attr) or "").strip(), []).append(r)
        ent_groups = []
        for acc, arows in by_acc.items():
            if not acc or len(arows) < 2:
                continue
            for keeper, removals in _group_dupes(arows, match, cols):
                ent_groups.append({
                    "account_no": acc,
                    "customer_name": name_by_acc.get(acc, ""),
                    "keeper": {"id": keeper.id, "summary": summ(keeper)},
                    "removals": [{"id": r.id, "summary": summ(r)} for r in removals],
                    "conflict_fields": _conflict(keeper, removals, cols),
                    "reason": _match_reason(keeper, removals[0]) if removals else "",
                })
                total_removals += len(removals)
        groups[key] = ent_groups
        counts[key] = sum(len(g["removals"]) for g in ent_groups)

    # Facilities — REVIEW ONLY (never auto-removed).
    fac_rows = list((await db.execute(
        select(Facility).where(Facility.is_deleted == False))).scalars().all())  # noqa: E712
    fac_cols = _data_cols(Facility)
    by_cust: dict[str, list] = {}
    for r in fac_rows:
        by_cust.setdefault(r.customer_id, []).append(r)
    cust_acc = dict((await db.execute(select(Customer.id, Customer.account_no))).all())
    fac_review = []
    for cid, frows in by_cust.items():
        if len(frows) < 2:
            continue
        for keeper, removals in _group_dupes(frows, _fac_match, fac_cols):
            acc = (cust_acc.get(cid) or "")
            fac_review.append({
                "account_no": acc, "customer_name": name_by_acc.get(acc, ""),
                "rows": [{"id": x.id, "summary": _fac_summary(x)} for x in [keeper, *removals]],
            })

    counts["facilities_review"] = sum(len(g["rows"]) for g in fac_review)
    counts["total_removals"] = total_removals
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "groups": groups,
        "review": {"facilities": fac_review},
        "counts": counts,
    }


_MODEL_BY_KEY = {k: (m, audit, label) for (k, m, _a, audit, label, _mt, _s) in _ENTITIES}


# ---------------------------------------------------------------------------
# Import / entry-time guard helpers (shared by crm._add_child & imports.py)
# ---------------------------------------------------------------------------
# Map a model to its duplicate matcher so any code that ADDS a record can reuse
# the exact same rules the cleanup engine uses — preventing duplicates at the
# point of entry (import, manual add, or AI-entered data) instead of only
# cleaning them up afterwards.
_MATCH_BY_MODEL = {
    MortgagedProperty: _props_match,
    FixedDeposit: _fd_match,
    Partner: _partner_match,
    Guarantor: _guar_match,
    Facility: _fac_match,
}


def matcher_for(model):
    """The duplicate-matcher callable for a model, or None if it has no rule."""
    return _MATCH_BY_MODEL.get(model)


def find_duplicate(candidate, existing_rows, model=None, match=None):
    """Return the first row in ``existing_rows`` that is a duplicate of
    ``candidate`` per the model's matcher, else ``None``.

    ``candidate`` is a (possibly transient, not-yet-added) model instance. The
    matcher never raises out of this helper — a comparison error just means "not
    a match" so a guard can never break the underlying add."""
    match = match or matcher_for(model or type(candidate))
    if not match:
        return None
    for r in existing_rows:
        if r is candidate:
            continue
        try:
            if match(r, candidate):
                return r
        except Exception:
            continue
    return None


def merge_fill(existing, incoming, model=None) -> list[str]:
    """Enrich ``existing`` with any non-empty fields from ``incoming`` that are
    currently empty on ``existing`` — never overwriting a populated field, so a
    merge can never introduce a contradiction. Returns the filled field names."""
    filled = []
    for c in _data_cols(model or type(existing)):
        if not _nz(getattr(existing, c, None)) and _nz(getattr(incoming, c, None)):
            setattr(existing, c, getattr(incoming, c))
            filled.append(c)
    return filled


async def apply(db: AsyncSession, user, only: list[str] | None = None) -> dict:
    """Re-scan (deterministic) and SOFT-DELETE the duplicate removals, logging each
    per-customer. ``only`` optionally limits which entity keys are applied."""
    from app.services.audit import record_audit

    report = await scan(db)
    removed: dict[str, int] = {}
    for key, ent_groups in report["groups"].items():
        if only and key not in only:
            continue
        model, audit_type, label = _MODEL_BY_KEY[key]
        ids = [rm["id"] for g in ent_groups for rm in g["removals"]]
        id_to_group = {rm["id"]: g for g in ent_groups for rm in g["removals"]}
        if not ids:
            continue
        rows = list((await db.execute(select(model).where(model.id.in_(ids)))).scalars().all())
        cnt = 0
        for r in rows:
            if getattr(r, "is_deleted", False):
                continue
            r.is_deleted = True
            cnt += 1
            g = id_to_group.get(r.id, {})
            await record_audit(
                action="delete", entity_type=audit_type, entity_id=r.id,
                account_no=g.get("account_no"),
                detail=f"پاک‌سازیِ خودکار — حذفِ {label}ِ تکراری (نگه‌داشته‌شده: {g.get('keeper', {}).get('id', '')})",
                user=user, db=db,
            )
        removed[key] = cnt
    await db.commit()
    removed["total"] = sum(removed.values())
    return {"applied_at": datetime.now(timezone.utc).isoformat(), "removed": removed}


# ---- optional AI «second opinion» (advisory only) ----
def _parse_groups(text: str, valid: set[str]) -> list[list[str]]:
    """Pull {"groups": [[id,id],...]} out of a model reply, keeping only known ids."""
    try:
        m = re.search(r"\{.*\}", text or "", re.S)
        data = json.loads(m.group() if m else text)
        out = []
        for g in (data.get("groups") or []):
            ids = [str(x) for x in g if str(x) in valid]
            if len(ids) >= 2:
                out.append(sorted(set(ids)))
        return out
    except Exception:
        return []


async def ai_second_opinion(db: AsyncSession, max_accounts: int = 15) -> dict:
    """Ask the active model to flag near-duplicates the rules didn't merge. Advisory
    only (never auto-applied). Best-effort: ``{available:False}`` if no model/network."""
    from app.ai.inference import complete

    probe = await complete(db, "reply exactly: ok", task="data_validation", max_tokens=5)
    if not probe.get("ok"):
        return {"available": False, "reason": probe.get("error", "no_model"),
                "note": "هیچ مدلِ هوش مصنوعیِ فعالی در دسترس نیست (یا شبکه مسدود است)."}

    specs = [("properties", MortgagedProperty, "املاک", _prop_summary),
             ("partners", Partner, "شرکا", _partner_summary),
             ("guarantors", Guarantor, "ضامن‌ها", _guar_summary)]
    suggestions, calls = [], 0
    for key, model, label, summ in specs:
        rows = list((await db.execute(select(model).where(model.is_deleted == False))).scalars().all())  # noqa: E712
        by_acc: dict[str, list] = {}
        for r in rows:
            by_acc.setdefault((r.account_no or "").strip(), []).append(r)
        for acc, arows in by_acc.items():
            if calls >= max_accounts:
                break
            if not acc or len(arows) < 2:
                continue
            items = [{"id": r.id, "info": summ(r)} for r in arows]
            prompt = (f"این فهرستِ رکوردهای «{label}» برای یک حساب بانکی است. کدام رکوردها در واقع یک مورد هستند (تکراری)؟ "
                      "فقط و فقط JSON برگردان: {\"groups\": [[\"id1\",\"id2\"]]} — هر گروه شناسه‌هایِ تکراری. اگر تکراری نبود: {\"groups\": []}.\n"
                      + json.dumps(items, ensure_ascii=False))
            calls += 1
            res = await complete(db, prompt, task="data_validation", max_tokens=500)
            if not res.get("ok"):
                continue
            for g in _parse_groups(res.get("text", ""), {r.id for r in arows}):
                suggestions.append({"entity": key, "label": label, "account_no": acc,
                                    "ids": g, "items": [i for i in items if i["id"] in g]})
        if calls >= max_accounts:
            break
    return {"available": True, "model": probe.get("model"), "suggestions": suggestions,
            "note": "پیشنهادِ هوش مصنوعی — فقط برای بازبینی؛ چیزی خودکار حذف نمی‌شود."}


# ---------------------------------------------------------------------------
# Background scheduler — REVIEW FIRST (a scheduled run never auto-deletes)
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# The loop wakes on this cadence and only acts when a run is actually due, so a
# schedule change made in the UI takes effect within one check.
_CHECK_INTERVAL_SECONDS = 3600
_INITIAL_DELAY_SECONDS = 300  # let boot work (seeds/reconcile) settle first
_SCHEDULE_SECONDS = {"daily": 86400, "weekly": 7 * 86400, "monthly": 30 * 86400}


async def _read_setting(db: AsyncSession, key: str, default: str = "") -> str:
    from app.models.system_setting import SystemSetting

    row = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    return row.value if row and row.value is not None else default


async def _write_setting(db: AsyncSession, key: str, value: str) -> None:
    from app.models.system_setting import SystemSetting

    row = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    if row:
        row.value = str(value)
    else:
        db.add(SystemSetting(key=key, value=str(value)))


def _schedule_due(schedule: str, last_run_iso: str, now: datetime) -> bool:
    """Whether a scheduled scan is due given the schedule + last-run timestamp."""
    interval = _SCHEDULE_SECONDS.get((schedule or "").strip().lower())
    if not interval:
        return False  # 'off' or unknown → never
    if not (last_run_iso or "").strip():
        return True   # never run before → due now
    try:
        last = datetime.fromisoformat(last_run_iso)
    except ValueError:
        return True   # unparseable → treat as never run
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (now - last).total_seconds() >= interval


async def _notify_admins(db: AsyncSession, *, title: str, message: str, level: str = "warning") -> None:
    """In-app notification to every active admin (falls back to a broadcast)."""
    from app.models.user import User, ROLE_ADMIN
    from app.services.notify_inapp import create_notification

    admins = list((await db.execute(
        select(User.id).where(
            ((User.role == ROLE_ADMIN) | (User.is_admin == True)),  # noqa: E712
            User.is_active == True,  # noqa: E712
        ))).scalars().all())
    for uid in (admins or [None]):  # no admins? broadcast so it isn't lost
        await create_notification(title=title, message=message, user_id=uid,
                                  level=level, link="/cleanup", category="system", db=db)


async def run_once_scheduled(db: AsyncSession) -> dict | None:
    """Run a single REVIEW-FIRST scheduled scan when the schedule says one is due.

    Produces a report + a ``CleanupRun(kind='scheduled')`` and notifies admins
    when there is something to review. It NEVER deletes anything — the user chose
    review-first, so a human still approves the actual removal on the Cleanup
    page. Returns the report when a run happened, else ``None``.
    """
    from app.models.cleanup_run import CleanupRun

    now = datetime.now(timezone.utc)
    schedule = await _read_setting(db, "cleanup_schedule", "off")
    last_run = await _read_setting(db, "cleanup_last_run", "")
    if not _schedule_due(schedule, last_run, now):
        return None

    report = await scan(db)
    counts = report["counts"]
    total = counts.get("total_removals", 0)
    fac = counts.get("facilities_review", 0)

    db.add(CleanupRun(
        kind="scheduled", trigger="schedule", username="system",
        counts_json=json.dumps(counts, ensure_ascii=False),
        detail=f"اسکنِ زمان‌بندی‌شده ({schedule}) — {total} رکوردِ تکراری برای بازبینی",
    ))
    await _write_setting(db, "cleanup_last_run", now.isoformat())
    await db.commit()

    if total or fac:
        await _notify_admins(
            db,
            title="پاک‌سازیِ دیتابیس: مواردی برای بازبینی پیدا شد",
            message=(f"اسکنِ زمان‌بندی‌شدهٔ دیتابیس {total} رکوردِ تکراری و {fac} تسهیلاتِ "
                     "نیازمندِ بررسی یافت. برای تأیید و حذف به صفحهٔ «پاک‌سازیِ دیتابیس» بروید."),
            level="warning",
        )
    logger.info("Scheduled cleanup scan complete (%s): %s", schedule, counts)
    return report


async def run_cleanup_scheduler() -> None:
    """Background loop: a review-first cleanup scan on the configured schedule.

    Started from the app lifespan. Wakes ~hourly and only acts when a run is due,
    so a schedule change from the UI takes effect within the hour. Opens its own
    DB session per check and swallows all errors so a transient failure never
    kills the loop. Cancellation (app shutdown) is propagated cleanly.

    Best-effort on constrained hosting: if the instance sleeps/restarts before a
    check fires, the "due" logic simply catches up on the next check.
    """
    from app.database import AsyncSessionLocal

    logger.info("Database-cleanup scheduler started (review-first, checks hourly)")
    delay = _INITIAL_DELAY_SECONDS
    while True:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            logger.info("Database-cleanup scheduler stopped")
            raise
        delay = _CHECK_INTERVAL_SECONDS  # subsequent checks are hourly
        try:
            async with AsyncSessionLocal() as session:
                await run_once_scheduled(session)
        except asyncio.CancelledError:
            logger.info("Database-cleanup scheduler stopped")
            raise
        except Exception as exc:  # pragma: no cover - keep the loop alive
            logger.error("Scheduled cleanup iteration failed: %s", exc)
