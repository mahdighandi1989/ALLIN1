"""Helpers for the per-facility credit-file checklist.

The Excel system gives each facility its own 9-step checklist (LoadFacilityChecklist)
and stamps an hourglass on every step the moment a facility is created (requirement
A24), so the user can tick each off as it is done. ``seed_facility_checklist`` is the
single place that creates that initial hourglass row, shared by both the CRM
quick-add and the main facilities create endpoint.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select, update

from app.models.crm import FacilityChecklist, CustomTask

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
