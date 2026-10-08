"""Helpers for the per-facility credit-file checklist.

The Excel system gives each facility its own 9-step checklist (LoadFacilityChecklist)
and stamps an hourglass on every step the moment a facility is created (requirement
A24), so the user can tick each off as it is done. ``seed_facility_checklist`` is the
single place that creates that initial hourglass row, shared by both the CRM
quick-add and the main facilities create endpoint.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select, update

from app.models.crm import FacilityChecklist, CustomTask, CHECKLIST_STEPS

# Marker stamped on every step of a brand-new facility's checklist (vs "✓" = done).
HOURGLASS = "⌛"


async def seed_facility_checklist(db, account_no: str, facility_id: str, username: str = ""):
    """Create a facility's checklist with an hourglass on every step. Idempotent:
    returns the existing row if one is already present for this facility."""
    fid = str(facility_id or "").strip()
    if not fid:
        return None
    existing = (
        await db.execute(select(FacilityChecklist).where(FacilityChecklist.facility_id == fid))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    fc = FacilityChecklist(
        id=f"FC-{fid}",
        account_no=account_no or "",
        facility_id=fid,
        total="0",
        last_action=date.today().isoformat(),
        last_user=username or "",
        is_deleted=False,
        **{f"item{i}": HOURGLASS for i in range(1, 10)},
    )
    db.add(fc)
    return fc


async def cascade_delete_facility(db, facility_id: str) -> None:
    """When a facility is removed, soft-delete its checklist and deactivate its
    follow-up tasks so they drop out of the pending list (requirement A5)."""
    fid = str(facility_id or "").strip()
    if not fid:
        return
    await db.execute(
        update(FacilityChecklist).where(FacilityChecklist.facility_id == fid).values(is_deleted=True)
    )
    await db.execute(
        update(CustomTask).where(CustomTask.facility_id == fid).values(is_active="0")
    )


async def cascade_restore_facility(db, facility_id: str) -> None:
    """Re-activate a facility's checklist when the facility itself is restored."""
    fid = str(facility_id or "").strip()
    if not fid:
        return
    await db.execute(
        update(FacilityChecklist).where(FacilityChecklist.facility_id == fid).values(is_deleted=False)
    )


# Facilities that are finished with do not need a complete credit file chased.
_SETTLED_STATUSES = {"closed", "inactive", "written_off"}
# Per-facility bell alerts per scan; beyond this a single summary stands in so a
# first scan over legacy data cannot bury the bell.
MAX_FACILITY_ALERTS = 25


def missing_steps(fc) -> list[str]:
    """Names of the checklist steps not yet ticked (``fc`` may be None = all)."""
    out = []
    for i, name in enumerate(CHECKLIST_STEPS, start=1):
        v = getattr(fc, f"item{i}", "") if fc is not None else ""
        if not (v == "✓" or v is True or str(v).lower() in ("true", "1")):
            out.append(name)
    return out


async def scan_incomplete_checklists(db, today: date | None = None) -> dict:
    """Raise a bell notification for every live facility whose own checklist is
    not fully ticked, naming exactly what is missing and linking straight to
    that facility's checklist. Facilities with no checklist row count as all
    pending. Idempotent: one unread alert per facility (category
    ``checklist:<facility_id>``), refreshed at most once a day; an alert whose
    facility has since been completed is marked read."""
    from app.models.customer import Customer
    from app.models.facility import Facility
    from app.models.notification import Notification

    today = today or date.today()
    start = datetime.combine(today, datetime.min.time())
    rows = (
        await db.execute(
            select(Facility, Customer.id, Customer.account_no)
            .join(Customer, Facility.customer_id == Customer.id)
            .where(Facility.is_deleted == False)  # noqa: E712
            .order_by(Facility.created_at.desc())
        )
    ).all()
    checklists = {
        fc.facility_id: fc
        for fc in (
            await db.execute(select(FacilityChecklist).where(FacilityChecklist.is_deleted == False))  # noqa: E712
        ).scalars().all()
    }
    open_alerts = {
        n.category: n
        for n in (
            await db.execute(
                select(Notification).where(
                    Notification.category.like("checklist:%"), Notification.is_read == False  # noqa: E712
                )
            )
        ).scalars().all()
    }
    incomplete = created = refreshed = resolved = 0
    still_open: set = set()
    for fac, cust_id, acc in rows:
        st = str(getattr(fac.status, "value", fac.status) or "").lower()
        if st in _SETTLED_STATUSES:
            continue
        gaps = missing_steps(checklists.get(fac.id))
        if not gaps:
            continue
        incomplete += 1
        cat = f"checklist:{fac.id}"
        still_open.add(cat)
        label = fac.name or str(getattr(fac.facility_type, "value", fac.facility_type) or "facility")
        title = f"Checklist incomplete — {label} ({fac.id})"[:200]
        message = f"Account {acc}: {len(gaps)}/{len(CHECKLIST_STEPS)} steps missing — " + ", ".join(gaps)
        link = f"/customer-detail/?id={cust_id}&tab=checklist&chk={fac.id}"
        existing = open_alerts.get(cat)
        if existing is not None:
            existing.title, existing.message, existing.link = title, message, link
            refreshed += 1
            continue
        if created >= MAX_FACILITY_ALERTS:
            continue
        db.add(Notification(user_id=None, level="warning", title=title, message=message,
                            link=link, category=cat, is_read=False))
        created += 1
    for cat, n in open_alerts.items():
        if cat not in still_open:
            n.is_read = True
            resolved += 1
    deferred = max(0, incomplete - len(open_alerts.keys() & still_open) - created)
    if deferred:
        summary_cat = "checklist-summary"
        already = (
            await db.execute(
                select(Notification).where(Notification.category == summary_cat,
                                           Notification.created_at >= start)
            )
        ).scalars().first()
        if already is None:
            db.add(Notification(
                user_id=None, level="warning",
                title=f"{incomplete} facilities have an incomplete checklist",
                message=f"{deferred} more not individually listed yet; open each customer's Checklist tab.",
                link="/customers", category=summary_cat, is_read=False))
    await db.commit()
    return {"incomplete": incomplete, "alerts_created": created,
            "alerts_refreshed": refreshed, "alerts_resolved": resolved, "deferred": deferred}
