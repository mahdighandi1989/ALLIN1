"""Filterable search over the activity logs for the AI surfaces.

The SEARCH itself covers the WHOLE ``audit_logs`` and ``journal_entries``
tables — no newest-N pre-limit — so nothing old is unreachable. Only the
rows RETURNED to the prompt have a token-safety ceiling, and the TRUE total
match count is always reported alongside, so a cut is never silent: the
model sees «۱۲۳۴ مورد یافت شد، ۵۰۰ موردِ نخست ارسال شد» and can narrow the
filter (text/user/action/date range/account) to reach any slice it needs.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import func, or_, select

# Token-safety ceiling on RETURNED rows only (the scan itself is unbounded).
MAX_LOG_ROWS = 500


def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _parse_date(raw: str):
    """Best-effort ISO date ('YYYY-MM-DD' or full timestamp) → datetime | None."""
    t = _s(raw)[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    return None


def sanitize_query(raw: Any) -> Dict[str, str]:
    """Clamp a model-supplied need_logs/logs_filter object to plain, short
    string filters. Unknown keys are dropped; nothing here reaches SQL as
    anything but a bound parameter."""
    raw = raw if isinstance(raw, dict) else {}
    out: Dict[str, str] = {}
    for key, cap in (("scope", 10), ("account_no", 50), ("text", 120), ("user", 80),
                     ("action", 50), ("date_from", 25), ("date_to", 25)):
        v = _s(raw.get(key))[:cap]
        if v:
            out[key] = v
    if out.get("scope") not in ("audit", "journal", "both"):
        out["scope"] = "both"
    return out


async def search_logs(db, q: Dict[str, str], limit: int = MAX_LOG_ROWS) -> Dict[str, Any]:
    """Run the (sanitized) log search. Returns compact rows, newest first,
    plus the true total counts and human warnings for any ceiling cut."""
    from app.models.audit_log import AuditLog
    from app.models.crm import JournalEntry

    q = sanitize_query(q)
    limit = max(1, min(int(limit or MAX_LOG_ROWS), MAX_LOG_ROWS))
    scope = q.get("scope", "both")
    d_from = _parse_date(q.get("date_from", ""))
    d_to = _parse_date(q.get("date_to", ""))
    if d_to and len(_s(q.get("date_to"))) <= 10:
        d_to = d_to + timedelta(days=1)  # inclusive end date
    out: Dict[str, Any] = {"query": q, "warnings": []}

    def _like(term: str) -> str:
        return f"%{term}%"

    if scope in ("audit", "both"):
        conds = []
        if q.get("account_no"):
            conds.append(AuditLog.account_no == q["account_no"])
        if q.get("user"):
            conds.append(AuditLog.username.ilike(_like(q["user"])))
        if q.get("action"):
            conds.append(AuditLog.action.ilike(_like(q["action"])))
        if q.get("text"):
            conds.append(or_(AuditLog.detail.ilike(_like(q["text"])),
                             AuditLog.entity_type.ilike(_like(q["text"]))))
        if d_from is not None:
            conds.append(AuditLog.created_at >= d_from)
        if d_to is not None:
            conds.append(AuditLog.created_at < d_to)
        total = (await db.execute(select(func.count()).select_from(AuditLog).where(*conds))).scalar() or 0
        rows = (
            await db.execute(
                select(AuditLog).where(*conds)
                .order_by(AuditLog.created_at.desc()).limit(limit)
            )
        ).scalars().all()
        out["audit_total"] = int(total)
        out["audit"] = [
            {"when": _s(a.created_at), "user": _s(a.username), "action": _s(a.action),
             "entity": _s(a.entity_type), "account_no": _s(a.account_no),
             "detail": _s(a.detail)[:300]}
            for a in rows
        ]
        if total > len(rows):
            out["warnings"].append(
                f"لاگِ کلی: {total} مورد با این فیلتر یافت شد؛ {len(rows)} موردِ جدیدتر ارسال شد — "
                "برای بقیه فیلتر را تنگ‌تر کن (متن/کاربر/بازهٔ تاریخ)."
            )

    if scope in ("journal", "both"):
        conds = []
        if q.get("account_no"):
            conds.append(JournalEntry.account_no == q["account_no"])
        if q.get("user"):
            conds.append(JournalEntry.user.ilike(_like(q["user"])))
        if q.get("action"):
            conds.append(JournalEntry.action.ilike(_like(q["action"])))
        if q.get("text"):
            conds.append(or_(JournalEntry.item.ilike(_like(q["text"])),
                             JournalEntry.notes.ilike(_like(q["text"])),
                             JournalEntry.category.ilike(_like(q["text"]))))
        if d_from is not None:
            conds.append(JournalEntry.created_at >= d_from)
        if d_to is not None:
            conds.append(JournalEntry.created_at < d_to)
        total = (await db.execute(select(func.count()).select_from(JournalEntry).where(*conds))).scalar() or 0
        rows = (
            await db.execute(
                select(JournalEntry).where(*conds)
                .order_by(JournalEntry.created_at.desc()).limit(limit)
            )
        ).scalars().all()
        out["journal_total"] = int(total)
        out["journal"] = [
            {"account_no": _s(j.account_no), "customer_name": _s(j.account_name),
             "branch": _s(j.branch), "category": _s(j.category), "item": _s(j.item),
             "status": _s(j.status), "date": _s(j.date), "time": _s(j.time),
             "user": _s(j.user), "action": _s(j.action), "notes": _s(j.notes)[:300]}
            for j in rows
        ]
        if total > len(rows):
            out["warnings"].append(
                f"لاگِ کارها: {total} مورد با این فیلتر یافت شد؛ {len(rows)} موردِ جدیدتر ارسال شد — "
                "برای بقیه فیلتر را تنگ‌تر کن."
            )

    return out
