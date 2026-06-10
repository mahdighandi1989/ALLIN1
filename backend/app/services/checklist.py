"""Helpers for the per-facility credit-file checklist.

The Excel system gives each facility its own 9-step checklist (LoadFacilityChecklist)
and stamps an hourglass on every step the moment a facility is created (requirement
A24), so the user can tick each off as it is done. ``seed_facility_checklist`` is the
single place that creates that initial hourglass row, shared by both the CRM
quick-add and the main facilities create endpoint.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.models.crm import FacilityChecklist

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
        **{f"item{i}": HOURGLASS for i in range(1, 10)},
    )
    db.add(fc)
    return fc
