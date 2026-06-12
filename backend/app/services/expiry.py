"""Expiry scanning — turn upcoming document/facility expiries into actionable
alerts (requirement A14).

For every facility and KYC document whose expiry falls within the configurable
``expiry_warning_days`` window (or is already past), this records a HIGH-priority
follow-up task on the owning customer (so it shows up in their task / pending
list) and posts a single broadcast notification per day. Tasks are upserted under
a STABLE id per item, so re-running the scan refreshes the message instead of
piling up duplicates.

There is no always-on worker in this deployment, so the scan runs at startup
(idempotent, once/day) and can be triggered on demand via
``POST /api/crm/run-expiry-scan`` (the web equivalent of the Excel
CheckAllExpiriesAndCreateAlerts macro).
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime

from sqlalchemy import and_, func, or_, select

from app.models.customer import Customer
from app.models.facility import Facility
from app.models.crm import CustomTask, CustomerProfile
from app.models.system_setting import SystemSetting
from app.models.notification import Notification

_KYC_DOCS = [
    ("Trade Licence", "trade_license_expiry"),
    ("Passport", "passport_expiry"),
    ("Emirates ID", "emirates_id_expiry"),
    ("Visa", "visa_expiry"),
    ("Tenancy", "tenancy_expiry"),
]


def _alert_id(kind: str, ref: str) -> str:
    """A stable, bounded CustomTask id for an expiry alert on one item."""
    return "ALERT-" + hashlib.md5(f"{kind}:{ref}".encode()).hexdigest()[:20]


def _parse_date(s):
    s = str(s or "").strip()[:10]
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            d = datetime.strptime(s, fmt).date()
            if 2000 <= d.year <= 2100:
                return d
        except ValueError:
            continue
    return None


async def _warning_days(db) -> int:
    row = (
        await db.execute(select(SystemSetting).where(SystemSetting.key == "expiry_warning_days"))
    ).scalar_one_or_none()
    try:
        return int((getattr(row, "value", None) or "30") or "30")
    except (ValueError, TypeError):
        return 30


async def _upsert_alert(db, *, key: str, account_no: str, facility_id: str, task_name: str, followup: str, notes: str) -> bool:
    """Create or refresh the alert task for one item. Returns True if newly created."""
    aid = _alert_id("alert", key)
    existing = (await db.execute(select(CustomTask).where(CustomTask.id == aid))).scalar_one_or_none()
    if existing is not None:
        existing.task_name = task_name[:200]
        existing.followup_date = (followup or "")[:30]
        existing.notes = notes
        existing.is_active = "1"
        return False
    db.add(CustomTask(
        id=aid, account_no=account_no, facility_id=(facility_id or "")[:60],
        task_name=task_name[:200], status="", followup_date=(followup or "")[:30],
        notes=notes, priority="High", created_by="system",
        created_date=date.today().isoformat(), completed_date="", is_active="1",
    ))
    return True


async def run_expiry_scan(db, warning_days: int | None = None) -> dict:
    """Scan facilities + KYC documents and raise/refresh expiry alert tasks."""
    today = date.today()
    wd = warning_days if warning_days is not None else await _warning_days(db)
    created = updated = fac_alerts = doc_alerts = 0

    rows = (
        await db.execute(
            select(Facility, Customer.account_no)
            .join(Customer, Facility.customer_id == Customer.id)
            .where(Facility.is_deleted == False)  # noqa: E712
        )
    ).all()
    for fac, acc in rows:
        exp = fac.expiry_date or fac.end_date
        if not exp:
            continue
        days_left = (exp - today).days
        if days_left > wd:
            continue
        fac_alerts += 1
        state = "expired" if days_left < 0 else f"expires in {days_left}d"
        name = fac.name or (getattr(fac.facility_type, "value", fac.facility_type) or "facility")
        is_new = await _upsert_alert(
            db, key=f"fac|{fac.id}", account_no=acc or "", facility_id=fac.id,
            task_name=f"⚠ Facility '{name}' {state} ({exp.isoformat()})",
            followup=exp.isoformat(),
            notes=f"Auto expiry alert · {days_left} days · facility {fac.id}",
        )
        created += int(is_new)
        updated += int(not is_new)

    # Only profiles that actually carry a KYC expiry date matter here. Select just
    # those few date columns (never the full row + its data_json) and let the DB
    # filter out the vast majority that have none — otherwise loading all ~44k
    # profiles as ORM objects OOMs the 512MB instance.
    expiry_cols = (
        CustomerProfile.trade_license_expiry,
        CustomerProfile.passport_expiry,
        CustomerProfile.emirates_id_expiry,
        CustomerProfile.visa_expiry,
        CustomerProfile.tenancy_expiry,
    )  # same order as _KYC_DOCS, so row[1:] zips cleanly with it
    rows = (
        await db.execute(
            select(CustomerProfile.account_no, *expiry_cols).where(
                or_(*[and_(c.isnot(None), c != "") for c in expiry_cols])
            )
        )
    ).all()
    for row in rows:
        acc = row[0]
        for (label, attr), value in zip(_KYC_DOCS, row[1:]):
            exp = _parse_date(value)
            if not exp:
                continue
            days_left = (exp - today).days
            if days_left > wd:
                continue
            doc_alerts += 1
            state = "expired" if days_left < 0 else f"expires in {days_left}d"
            is_new = await _upsert_alert(
                db, key=f"doc|{acc}|{attr}", account_no=acc or "", facility_id="",
                task_name=f"⚠ {label} {state} ({exp.isoformat()})",
                followup=exp.isoformat(),
                notes=f"Auto expiry alert · {days_left} days · {label}",
            )
            created += int(is_new)
            updated += int(not is_new)

    total = fac_alerts + doc_alerts
    if total:
        start = datetime.combine(today, datetime.min.time())
        already = (
            await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.category == "expiry-scan",
                    Notification.created_at >= start,
                )
            )
        ).scalar() or 0
        if not already:
            db.add(Notification(
                user_id=None, level="warning",
                title=f"{total} expiry alerts ({fac_alerts} facilities, {doc_alerts} documents)",
                message=f"Items expiring within {wd} days are flagged in the customers' task lists.",
                link="/dashboard", category="expiry-scan", is_read=False,
            ))
            # Mirror the alert to Telegram (best-effort; respects panel prefs).
            try:
                from app.services.telegram import telegram_service

                await telegram_service.notify_event(
                    "expiry_scan_summary",
                    f"🔁 اسکن انقضا: *{total}* آلرت "
                    f"({fac_alerts} تسهیلات، {doc_alerts} مدرک) در پنجرهٔ {wd} روز.",
                    priority="high" if fac_alerts else "medium",
                )
            except Exception as exc:  # never break the scan on a notify failure
                import logging
                logging.getLogger(__name__).warning("expiry telegram notify failed: %s", exc)

    await db.commit()
    return {
        "warning_days": wd, "facilities": fac_alerts, "documents": doc_alerts,
        "tasks_created": created, "tasks_updated": updated, "total": total,
    }
