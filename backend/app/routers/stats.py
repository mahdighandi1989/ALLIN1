"""Stats Router - Dashboard Data"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Customer, Facility, CustomerStatus, FacilityStatus
from app.utils.security import get_current_user, TokenData

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics"""
    # Customers
    total_customers = (await db.execute(
        select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
    )).scalar() or 0

    active_customers = (await db.execute(
        select(func.count()).select_from(Customer).where(
            Customer.is_deleted == False,
            Customer.status == CustomerStatus.ACTIVE
        )
    )).scalar() or 0

    # Facilities
    total_facilities = (await db.execute(
        select(func.count()).select_from(Facility).where(Facility.is_deleted == False)
    )).scalar() or 0

    total_amount = (await db.execute(
        select(func.sum(Facility.amount)).where(Facility.is_deleted == False)
    )).scalar() or 0

    total_outstanding = (await db.execute(
        select(func.sum(Facility.outstanding)).where(Facility.is_deleted == False)
    )).scalar() or 0

    # Expiring soon (30 days)
    expiry_cutoff = datetime.now().date() + timedelta(days=30)
    expiring_soon = (await db.execute(
        select(func.count()).select_from(Facility).where(
            Facility.is_deleted == False,
            Facility.status == FacilityStatus.ACTIVE,
            Facility.expiry_date <= expiry_cutoff,
            Facility.expiry_date >= datetime.now().date()
        )
    )).scalar() or 0

    # Recent customers
    recent = await db.execute(
        select(Customer)
        .where(Customer.is_deleted == False)
        .order_by(Customer.created_at.desc())
        .limit(5)
    )
    recent_customers = [
        {"id": c.id, "name": c.name, "account_no": c.account_no}
        for c in recent.scalars()
    ]

    return {
        "customers": {
            "total": total_customers,
            "active": active_customers
        },
        "facilities": {
            "total": total_facilities,
            "total_amount": float(total_amount),
            "outstanding": float(total_outstanding),
            "expiring_soon": expiring_soon
        },
        "recent_customers": recent_customers
    }


@router.get("/expiring")
async def get_expiring_facilities(
    days: int = 30,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get facilities expiring soon"""
    cutoff = datetime.now().date() + timedelta(days=days)

    result = await db.execute(
        select(Facility).where(
            Facility.is_deleted == False,
            Facility.status == FacilityStatus.ACTIVE,
            Facility.expiry_date <= cutoff,
            Facility.expiry_date >= datetime.now().date()
        ).order_by(Facility.expiry_date)
    )
    facilities = result.scalars().all()

    # Get customer names
    customer_ids = list(set(f.customer_id for f in facilities))
    customer_names = {}
    if customer_ids:
        customers = await db.execute(select(Customer).where(Customer.id.in_(customer_ids)))
        for c in customers.scalars():
            customer_names[c.id] = c.name

    return {
        "items": [
            {
                "id": f.id,
                "customer_id": f.customer_id,
                "customer_name": customer_names.get(f.customer_id),
                "facility_type": f.facility_type.value,
                "amount": float(f.amount) if f.amount else 0,
                "expiry_date": f.expiry_date.isoformat() if f.expiry_date else None,
                "days_until_expiry": (f.expiry_date - datetime.now().date()).days if f.expiry_date else None
            }
            for f in facilities
        ],
        "total": len(facilities)
    }
