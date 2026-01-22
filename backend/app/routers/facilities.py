"""Facilities Router"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Facility, FacilityType, FacilityStatus, Customer
from app.schemas import FacilityCreate, FacilityUpdate, FacilityResponse, FacilityList
from app.utils.security import get_current_user, TokenData

router = APIRouter(prefix="/api/facilities", tags=["Facilities"])


def facility_to_response(f: Facility, customer_name: str = None) -> dict:
    return {
        "id": f.id,
        "customer_id": f.customer_id,
        "customer_name": customer_name,
        "facility_type": f.facility_type.value if f.facility_type else "loan",
        "name": f.name,
        "status": f.status.value if f.status else "active",
        "amount": float(f.amount) if f.amount else 0,
        "outstanding": float(f.outstanding) if f.outstanding else 0,
        "currency": f.currency,
        "start_date": f.start_date,
        "expiry_date": f.expiry_date,
        "interest_rate": float(f.interest_rate) if f.interest_rate else None,
        "tenor_months": f.tenor_months,
        "notes": f.notes,
        "created_at": f.created_at,
        "updated_at": f.updated_at,
    }


@router.get("", response_model=FacilityList)
async def list_facilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: str = None,
    facility_type: str = None,
    status: str = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List facilities with pagination"""
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
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.order_by(Facility.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    facilities = result.scalars().all()

    # Get customer names
    customer_ids = list(set(f.customer_id for f in facilities))
    customer_names = {}
    if customer_ids:
        customers = await db.execute(select(Customer).where(Customer.id.in_(customer_ids)))
        for c in customers.scalars():
            customer_names[c.id] = c.name

    return FacilityList(
        items=[facility_to_response(f, customer_names.get(f.customer_id)) for f in facilities],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{facility_id}", response_model=FacilityResponse)
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
    customer = await db.execute(select(Customer).where(Customer.id == facility.customer_id))
    customer = customer.scalars().first()

    return facility_to_response(facility, customer.name if customer else None)


@router.post("", response_model=FacilityResponse)
async def create_facility(
    data: FacilityCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new facility"""
    # Check customer exists
    result = await db.execute(
        select(Customer).where(Customer.id == data.customer_id, Customer.is_deleted == False)
    )
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    facility = Facility(
        customer_id=data.customer_id,
        facility_type=FacilityType(data.facility_type),
        name=data.name,
        amount=data.amount,
        outstanding=data.amount,  # Start with full amount as outstanding
        currency=data.currency,
        start_date=data.start_date,
        expiry_date=data.expiry_date,
        interest_rate=data.interest_rate,
        tenor_months=data.tenor_months,
        notes=data.notes
    )
    db.add(facility)
    await db.commit()
    await db.refresh(facility)

    return facility_to_response(facility, customer.name)


@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: str,
    data: FacilityUpdate,
    current_user: TokenData = Depends(get_current_user),
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

    await db.commit()
    await db.refresh(facility)

    # Get customer name
    customer = await db.execute(select(Customer).where(Customer.id == facility.customer_id))
    customer = customer.scalars().first()

    return facility_to_response(facility, customer.name if customer else None)


@router.delete("/{facility_id}")
async def delete_facility(
    facility_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete facility (soft delete)"""
    result = await db.execute(
        select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    )
    facility = result.scalars().first()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    facility.is_deleted = True
    await db.commit()

    return {"message": "Facility deleted"}
