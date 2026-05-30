from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.schemas.facility import (
    FacilityCreate,
    FacilityUpdate,
    FacilityResponse,
    FacilityListResponse,
)
from app.utils.security import get_current_user

# Authentication is required for every facility endpoint. The prefix is provided
# by main.py (/api/facilities), so the router itself must not add another prefix.
router = APIRouter(tags=["facilities"], dependencies=[Depends(get_current_user)])

_FACILITY_NOT_FOUND = "Facility not found"
_CUSTOMER_NOT_FOUND = "Customer not found"


async def _get_active_facility(facility_id: str, db: AsyncSession) -> Facility:
    """Fetch a non-deleted facility or raise 404 (with a stable message)."""
    result = await db.execute(
        select(Facility).where(
            Facility.id == facility_id, Facility.is_deleted == False
        )
    )
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_FACILITY_NOT_FOUND
        )
    return facility


async def _ensure_customer_exists(customer_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id, Customer.is_deleted == False
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_CUSTOMER_NOT_FOUND
        )


@router.get("/", response_model=FacilityListResponse)
async def list_facilities(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    facility_type: Optional[FacilityType] = Query(None, description="Filter by facility type"),
    status: Optional[FacilityStatus] = Query(None, description="Filter by facility status"),
    search: Optional[str] = Query(None, description="Search term for facility name"),
):
    """Retrieve a paginated list of facilities with optional filtering."""
    base = select(Facility).where(Facility.is_deleted == False)

    if customer_id:
        base = base.where(Facility.customer_id == customer_id)
    if facility_type:
        base = base.where(Facility.facility_type == facility_type)
    if status:
        base = base.where(Facility.status == status)
    if search:
        base = base.where(Facility.name.ilike(f"%{search}%"))

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(Facility.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    facilities = result.scalars().all()

    return FacilityListResponse(
        items=facilities, total=total, page=page, page_size=page_size
    )


@router.get("/search/advanced", response_model=FacilityListResponse)
async def advanced_search_facilities(
    db: AsyncSession = Depends(get_db),
    amount_from: Optional[float] = Query(None, ge=0),
    amount_to: Optional[float] = Query(None, ge=0),
    date_from: Optional[date] = Query(None, description="Earliest start date"),
    date_to: Optional[date] = Query(None, description="Latest start date"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    facility_type: Optional[FacilityType] = Query(None),
    status: Optional[FacilityStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
):
    """Advanced facility search by amount range, start-date range and customer name."""
    base = select(Facility).where(Facility.is_deleted == False)

    if amount_from is not None:
        base = base.where(Facility.amount >= amount_from)
    if amount_to is not None:
        base = base.where(Facility.amount <= amount_to)
    if date_from is not None:
        base = base.where(Facility.start_date >= date_from)
    if date_to is not None:
        base = base.where(Facility.start_date <= date_to)
    if facility_type:
        base = base.where(Facility.facility_type == facility_type)
    if status:
        base = base.where(Facility.status == status)
    if customer_name:
        customer_ids = select(Customer.id).where(
            Customer.name.ilike(f"%{customer_name}%")
        )
        base = base.where(Facility.customer_id.in_(customer_ids))

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(Facility.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    facilities = result.scalars().all()
    return FacilityListResponse(
        items=facilities, total=total, page=page, page_size=page_size
    )


@router.get("/{facility_id}/detail")
async def get_facility_detail(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Full facility profile: the facility plus its customer's name/account."""
    facility = await _get_active_facility(facility_id, db)
    cust = (
        await db.execute(
            select(Customer.name, Customer.account_no).where(
                Customer.id == facility.customer_id
            )
        )
    ).first()
    return {
        "facility": FacilityResponse.model_validate(facility),
        "customer_name": cust[0] if cust else None,
        "customer_account_no": cust[1] if cust else None,
    }


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific facility by ID."""
    return await _get_active_facility(facility_id, db)


@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
async def create_facility(
    facility_data: FacilityCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new facility (after verifying the owning customer exists)."""
    await _ensure_customer_exists(facility_data.customer_id, db)

    new_facility = Facility(**facility_data.model_dump())
    db.add(new_facility)
    await db.commit()
    await db.refresh(new_facility)
    return new_facility


@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: str,
    facility_data: FacilityUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing facility."""
    facility = await _get_active_facility(facility_id, db)

    update_data = facility_data.model_dump(exclude_unset=True)
    if (
        update_data.get("customer_id")
        and update_data["customer_id"] != facility.customer_id
    ):
        await _ensure_customer_exists(update_data["customer_id"], db)

    for field, value in update_data.items():
        setattr(facility, field, value)

    await db.commit()
    await db.refresh(facility)
    return facility


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Soft delete a facility."""
    facility = await _get_active_facility(facility_id, db)
    facility.is_deleted = True
    await db.commit()
    return None


@router.post("/{facility_id}/restore", response_model=FacilityResponse)
async def restore_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Restore a previously soft-deleted facility and re-activate it."""
    result = await db.execute(
        select(Facility).where(
            Facility.id == facility_id, Facility.is_deleted == True
        )
    )
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_FACILITY_NOT_FOUND
        )

    facility.is_deleted = False
    facility.status = FacilityStatus.ACTIVE
    await db.commit()
    await db.refresh(facility)
    return facility


@router.patch("/{facility_id}/status")
async def update_facility_status(
    facility_id: str,
    new_status: FacilityStatus = Query(..., description="New facility status"),
    db: AsyncSession = Depends(get_db),
):
    """Update only the status of a facility."""
    facility = await _get_active_facility(facility_id, db)
    facility.status = new_status
    await db.commit()
    await db.refresh(facility)
    return {
        "message": f"Facility status updated to {new_status.value}",
        "id": facility.id,
        "status": facility.status.value,
    }
