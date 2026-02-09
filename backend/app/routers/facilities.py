# backend/app/routers/facilities.py

"""Facilities Router - CRUD operations for banking facilities"""
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Customer, Facility
from app.models.facility import FacilityType, FacilityStatus
from app.utils.security import get_optional_current_user

router = APIRouter()


# Schemas
class FacilityCreate(BaseModel):
    customer_id: str
    facility_type: FacilityType
    name: Optional[str] = None
    amount: Decimal = Field(..., description="Facility amount")
    outstanding: Optional[Decimal] = Field(default=0, description="Outstanding amount")
    currency: str = Field(default="AED")
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    tenor_months: Optional[str] = None
    notes: Optional[str] = None


class FacilityUpdate(BaseModel):
    facility_type: Optional[FacilityType] = None
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    outstanding: Optional[Decimal] = None
    currency: Optional[str] = None
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    tenor_months: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[FacilityStatus] = None


class FacilityResponse(BaseModel):
    id: str
    customer_id: str
    facility_type: FacilityType
    name: Optional[str]
    status: FacilityStatus
    amount: Decimal
    outstanding: Decimal
    currency: str
    start_date: Optional[date]
    expiry_date: Optional[date]
    interest_rate: Optional[Decimal]
    tenor_months: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_deleted: bool

    class Config:
        from_attributes = True


# Routes
@router.get("/", response_model=List[FacilityResponse])
async def list_facilities(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    facility_type: Optional[FacilityType] = Query(None, description="Filter by facility type"),
    status: Optional[FacilityStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """List all facilities with optional filters"""
    query = select(Facility).where(Facility.is_deleted == False)

    if customer_id:
        query = query.where(Facility.customer_id == customer_id)
    if facility_type:
        query = query.where(Facility.facility_type == facility_type)
    if status:
        query = query.where(Facility.status == status)

    query = query.offset(skip).limit(limit).order_by(desc(Facility.created_at))

    result = await db.execute(query)
    facilities = result.scalars().all()

    return [FacilityResponse.from_orm(f) for f in facilities]


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Get a specific facility by ID"""
    query = select(Facility).where(
        and_(
            Facility.id == facility_id,
            Facility.is_deleted == False
        )
    )
    result = await db.execute(query)
    facility = result.scalar_one_or_none()

    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )

    return FacilityResponse.from_orm(facility)


@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
async def create_facility(
    facility_data: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Create a new facility"""
    try:
        # Check if customer exists
        customer_query = select(Customer).where(
            and_(
                Customer.id == facility_data.customer_id,
                Customer.is_deleted == False
            )
        )
        customer_result = await db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )

        # Create facility with all fields including amount
        db_facility = Facility(
            customer_id=facility_data.customer_id,
            facility_type=facility_data.facility_type,
            name=facility_data.name,
            amount=facility_data.amount,
            outstanding=facility_data.outstanding or 0,
            currency=facility_data.currency,
            start_date=facility_data.start_date,
            expiry_date=facility_data.expiry_date,
            interest_rate=facility_data.interest_rate,
            tenor_months=facility_data.tenor_months,
            notes=facility_data.notes,
            status=FacilityStatus.ACTIVE,
            created_at=datetime.utcnow()
        )

        db.add(db_facility)
        await db.commit()
        await db.refresh(db_facility)

        return FacilityResponse.from_orm(db_facility)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create facility: {str(e)}"
        )


@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: str,
    facility_data: FacilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Update facility information"""
    try:
        # Check if facility exists
        query = select(Facility).where(
            and_(
                Facility.id == facility_id,
                Facility.is_deleted == False
            )
        )
        result = await db.execute(query)
        facility = result.scalar_one_or_none()

        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )

        # Update facility fields - amount is now properly supported
        update_data = facility_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(facility, field, value)

        facility.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(facility)

        return FacilityResponse.from_orm(facility)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update facility: {str(e)}"
        )


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facility(
    facility_id: str,
    permanent: bool = Query(False, description="Permanently delete (admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Delete a facility (soft delete by default)"""
    try:
        # Check if facility exists
        query = select(Facility).where(
            and_(
                Facility.id == facility_id,
                Facility.is_deleted == False
            )
        )
        result = await db.execute(query)
        facility = result.scalar_one_or_none()

        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )

        if permanent:
            # Permanent delete (would need admin role check)
            await db.delete(facility)
        else:
            # Soft delete
            facility.is_deleted = True
            facility.status = FacilityStatus.CLOSED
            facility.updated_at = datetime.utcnow()

        await db.commit()
        return None

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete facility: {str(e)}"
        )


@router.post("/{facility_id}/restore", response_model=FacilityResponse)
async def restore_facility(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Restore a soft-deleted facility"""
    try:
        # Find soft-deleted facility
        query = select(Facility).where(
            and_(
                Facility.id == facility_id,
                Facility.is_deleted == True
            )
        )
        result = await db.execute(query)
        facility = result.scalar_one_or_none()

        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deleted facility not found"
            )

        # Restore facility
        facility.is_deleted = False
        facility.status = FacilityStatus.ACTIVE
        facility.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(facility)

        return FacilityResponse.from_orm(facility)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore facility: {str(e)}"
        )


@router.patch("/{facility_id}/status")
async def update_facility_status(
    facility_id: str,
    new_status: FacilityStatus,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Update facility status"""
    try:
        query = select(Facility).where(
            and_(
                Facility.id == facility_id,
                Facility.is_deleted == False
            )
        )
        result = await db.execute(query)
        facility = result.scalar_one_or_none()

        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )

        facility.status = new_status
        facility.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(facility)

        return {"message": f"Facility status updated to {new_status.value}"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update facility status: {str(e)}"
        )


@router.get("/search/advanced")
async def advanced_search_facilities(
    customer_name: Optional[str] = Query(None, description="Search by customer name"),
    amount_from: Optional[float] = Query(None, description="Minimum amount"),
    amount_to: Optional[float] = Query(None, description="Maximum amount"),
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    expiry_from: Optional[date] = Query(None, description="Expiry date from"),
    expiry_to: Optional[date] = Query(None, description="Expiry date to"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Advanced search for facilities"""
    try:
        # Build query with joins and select customer name directly
        query = select(Facility, Customer.name.label("customer_name")).join(
            Customer, Facility.customer_id == Customer.id
        ).where(
            and_(
                Facility.is_deleted == False,
                Customer.is_deleted == False
            )
        )

        conditions = []

        if customer_name:
            conditions.append(Customer.name.ilike(f"%{customer_name}%"))

        # Amount filters - now properly supported
        if amount_from is not None:
            conditions.append(Facility.amount >= amount_from)

        if amount_to is not None:
            conditions.append(Facility.amount <= amount_to)

        if date_from:
            conditions.append(Facility.start_date >= date_from)

        if date_to:
            conditions.append(Facility.start_date <= date_to)

        if expiry_from:
            conditions.append(Facility.expiry_date >= expiry_from)

        if expiry_to:
            conditions.append(Facility.expiry_date <= expiry_to)

        if conditions:
            query = query.where(and_(*conditions))

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(desc(Facility.created_at))

        result = await db.execute(query)
        rows = result.all()

        # Build response
        facility_responses = []
        for facility, cust_name in rows:
            facility_dict = {
                "id": facility.id,
                "customer_id": facility.customer_id,
                "customer_name": cust_name,
                "facility_type": facility.facility_type.value if facility.facility_type else None,
                "name": facility.name,
                "status": facility.status.value if facility.status else None,
                "amount": float(facility.amount) if facility.amount else 0,
                "outstanding": float(facility.outstanding) if facility.outstanding else 0,
                "currency": facility.currency,
                "start_date": facility.start_date.isoformat() if facility.start_date else None,
                "expiry_date": facility.expiry_date.isoformat() if facility.expiry_date else None,
                "interest_rate": float(facility.interest_rate) if facility.interest_rate else None,
                "tenor_months": facility.tenor_months,
                "notes": facility.notes,
                "created_at": facility.created_at.isoformat() if facility.created_at else None,
                "updated_at": facility.updated_at.isoformat() if facility.updated_at else None,
            }
            facility_responses.append(facility_dict)

        return {
            "items": facility_responses,
            "total": len(facility_responses)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search facilities: {str(e)}"
        )
