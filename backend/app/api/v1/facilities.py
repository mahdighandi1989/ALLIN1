"""
Facilities API
API مدیریت تسهیلات
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import get_current_user, TokenData, require_permission
from app.core.database import get_db
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.customer import Customer

router = APIRouter()


class FacilityCreate(BaseModel):
    customer_id: str
    facility_type: str
    facility_name: Optional[str] = None
    approved_amount: Decimal
    currency: str = "AED"
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    notes: Optional[str] = None


class FacilityUpdate(BaseModel):
    facility_name: Optional[str] = None
    approved_amount: Optional[Decimal] = None
    outstanding_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


def facility_to_dict(f: Facility, customer_name: str = None) -> dict:
    return {
        "id": f.id,
        "customer_id": f.customer_id,
        "customer_name": customer_name,
        "facility_type": f.facility_type.value if hasattr(f.facility_type, 'value') else str(f.facility_type),
        "facility_name": f.facility_name,
        "approved_amount": float(f.approved_amount) if f.approved_amount else 0,
        "outstanding_amount": float(f.outstanding_amount) if f.outstanding_amount else 0,
        "currency": f.currency,
        "start_date": f.start_date.isoformat() if f.start_date else None,
        "expiry_date": f.expiry_date.isoformat() if f.expiry_date else None,
        "interest_rate": float(f.interest_rate) if f.interest_rate else None,
        "status": f.status.value if hasattr(f.status, 'value') else str(f.status),
        "notes": f.notes,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@router.get("/")
async def list_facilities(
    customer_id: Optional[str] = None,
    facility_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List facilities"""
    query = select(Facility).where(Facility.is_deleted == False)

    if customer_id:
        query = query.where(Facility.customer_id == customer_id)

    if facility_type:
        try:
            query = query.where(Facility.facility_type == FacilityType(facility_type))
        except ValueError:
            pass

    if status:
        try:
            query = query.where(Facility.status == FacilityStatus(status))
        except ValueError:
            pass

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Facility.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    facilities = result.scalars().all()

    # Get customer names
    customer_ids = list(set(f.customer_id for f in facilities))
    customer_names = {}
    if customer_ids:
        customers = await db.execute(
            select(Customer).where(Customer.id.in_(customer_ids))
        )
        for c in customers.scalars():
            customer_names[c.id] = c.customer_name

    return {
        "items": [facility_to_dict(f, customer_names.get(f.customer_id)) for f in facilities],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.post("/")
async def create_facility(
    data: FacilityCreate,
    current_user: TokenData = Depends(require_permission("write:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """Create facility"""
    # Verify customer exists
    result = await db.execute(
        select(Customer).where(Customer.id == data.customer_id, Customer.is_deleted == False)
    )
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Customer not found")

    facility = Facility(
        customer_id=data.customer_id,
        facility_type=FacilityType(data.facility_type),
        facility_name=data.facility_name,
        approved_amount=data.approved_amount,
        outstanding_amount=data.approved_amount,
        currency=data.currency,
        start_date=data.start_date,
        expiry_date=data.expiry_date,
        interest_rate=data.interest_rate,
        notes=data.notes,
        status=FacilityStatus.ACTIVE,
        created_by=current_user.user_id
    )

    db.add(facility)
    await db.commit()
    await db.refresh(facility)

    return facility_to_dict(facility)


@router.get("/{facility_id}")
async def get_facility(
    facility_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get facility by ID"""
    result = await db.execute(
        select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    )
    facility = result.scalars().first()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    # Get customer name
    customer = await db.execute(
        select(Customer).where(Customer.id == facility.customer_id)
    )
    customer = customer.scalars().first()

    return facility_to_dict(facility, customer.customer_name if customer else None)


@router.put("/{facility_id}")
async def update_facility(
    facility_id: str,
    data: FacilityUpdate,
    current_user: TokenData = Depends(require_permission("write:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """Update facility"""
    result = await db.execute(
        select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    )
    facility = result.scalars().first()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "status":
                value = FacilityStatus(value)
            setattr(facility, field, value)

    facility.updated_by = current_user.user_id
    await db.commit()
    await db.refresh(facility)

    return facility_to_dict(facility)


@router.delete("/{facility_id}")
async def delete_facility(
    facility_id: str,
    current_user: TokenData = Depends(require_permission("delete:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """Delete facility"""
    result = await db.execute(
        select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    )
    facility = result.scalars().first()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    facility.is_deleted = True
    facility.deleted_by = current_user.user_id
    await db.commit()

    return {"message": "Facility deleted successfully"}


@router.get("/stats/summary")
async def get_facility_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get facility statistics"""
    # Total
    total = (await db.execute(
        select(func.count()).select_from(Facility).where(Facility.is_deleted == False)
    )).scalar() or 0

    # Total amount
    total_amount = (await db.execute(
        select(func.sum(Facility.approved_amount)).where(Facility.is_deleted == False)
    )).scalar() or 0

    # Outstanding
    outstanding = (await db.execute(
        select(func.sum(Facility.outstanding_amount)).where(Facility.is_deleted == False)
    )).scalar() or 0

    # Expiring soon (30 days)
    from datetime import datetime, timedelta
    expiring = (await db.execute(
        select(func.count()).select_from(Facility).where(
            Facility.is_deleted == False,
            Facility.expiry_date <= datetime.now().date() + timedelta(days=30),
            Facility.expiry_date >= datetime.now().date()
        )
    )).scalar() or 0

    return {
        "total": total,
        "total_amount": float(total_amount),
        "outstanding_amount": float(outstanding),
        "expiring_soon": expiring
    }
