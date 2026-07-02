"""Recycle bin: list and restore soft-deleted records across entities.

Read endpoints surface everything with ``is_deleted = True``; restore flips the
flag back. Entity-specific restore logic (e.g. re-activating a facility) lives in
the owning routers; this provides a single consolidated view for the UI.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer, CustomerStatus
from app.models.facility import Facility, FacilityStatus
from app.models.offer_letter import OfferLetter
from app.utils.security import get_current_user
from app.routers.auth import require_editor
from app.services.checklist import cascade_restore_facility

router = APIRouter(tags=["trash"], dependencies=[Depends(get_current_user)])

_NOT_FOUND = "Deleted item not found"


@router.get("/")
async def list_trash(db: AsyncSession = Depends(get_db)):
    """Return all soft-deleted customers, facilities and offer letters."""
    customers = (
        await db.execute(select(Customer).where(Customer.is_deleted == True))
    ).scalars().all()
    facilities = (
        await db.execute(select(Facility).where(Facility.is_deleted == True))
    ).scalars().all()
    offers = (
        await db.execute(select(OfferLetter).where(OfferLetter.is_deleted == True))
    ).scalars().all()

    def cust(c):
        return {"id": str(c.id), "label": c.name or c.account_no or c.id,
                "sublabel": c.account_no, "type": "customer"}

    def fac(f):
        return {"id": str(f.id),
                "label": f.name or getattr(f.facility_type, "value", f.facility_type) or f.id,
                "sublabel": f"{f.currency or 'AED'} {float(f.amount or 0):,.0f}",
                "type": "facility"}

    def off(o):
        return {"id": str(o.id), "label": o.id,
                "sublabel": f"{o.currency or 'AED'} {float(o.principal_amount or 0):,.0f}",
                "type": "offer_letter"}

    items = (
        [cust(c) for c in customers]
        + [fac(f) for f in facilities]
        + [off(o) for o in offers]
    )
    return {
        "items": items,
        "total": len(items),
        "counts": {
            "customers": len(customers),
            "facilities": len(facilities),
            "offer_letters": len(offers),
        },
    }


@router.post("/{entity}/{item_id}/restore")
async def restore_item(
    entity: str,
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Restore a single soft-deleted item by entity type + id."""
    if entity in ("customer", "customers"):
        obj = (
            await db.execute(
                select(Customer).where(Customer.id == item_id, Customer.is_deleted == True)
            )
        ).scalar_one_or_none()
        if obj:
            obj.is_deleted = False
            obj.status = CustomerStatus.ACTIVE
    elif entity in ("facility", "facilities"):
        obj = (
            await db.execute(
                select(Facility).where(Facility.id == item_id, Facility.is_deleted == True)
            )
        ).scalar_one_or_none()
        if obj:
            obj.is_deleted = False
            obj.status = FacilityStatus.ACTIVE
            # Same behavior as facilities.py restore: bring the facility's
            # checklist/tasks back too, or credit-file workflow state is lost.
            await cascade_restore_facility(db, obj.id)
    elif entity in ("offer_letter", "offer_letters", "offer-letters"):
        obj = (
            await db.execute(
                select(OfferLetter).where(
                    OfferLetter.id == item_id, OfferLetter.is_deleted == True
                )
            )
        ).scalar_one_or_none()
        if obj:
            obj.is_deleted = False
    else:
        raise HTTPException(status_code=400, detail=f"Unknown entity type '{entity}'")

    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)

    await db.commit()
    return {"restored": True, "entity": entity, "id": item_id}
