from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.customer import Customer
from app.schemas.facility import FacilityCreate, FacilityUpdate, FacilityResponse
from app.utils.security import get_optional_current_user

router = APIRouter(prefix="/api/facilities", tags=["facilities"])


@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
async def create_facility(
    facility_data: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Create a new facility"""
    try:
        # Verify customer exists
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
        
        # Create facility - REMOVED amount field since it doesn't exist in database
        db_facility = Facility(
            customer_id=facility_data.customer_id,
            facility_type=facility_data.facility_type,
            name=facility_data.name,
            # amount=facility_data.amount,  # This column doesn't exist in the database
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


@router.get("/", response_model=dict)
async def get_facilities(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    facility_type: Optional[FacilityType] = Query(None, description="Filter by facility type"),
    status: Optional[FacilityStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in facility name"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Get list of facilities with filtering, pagination and sorting"""
    try:
        # Use page-based pagination if provided
        if page > 1:
            skip = (page - 1) * page_size
            limit = page_size
        
        # Build base query with join to get customer name in single query
        query = select(Facility, Customer.name.label("customer_name")).join(
            Customer, Facility.customer_id == Customer.id
        ).where(
            and_(
                Facility.is_deleted == False,
                Customer.is_deleted == False
            )
        )
        
        # Build count query with same filters
        count_query = select(func.count()).select_from(Facility).join(
            Customer, Facility.customer_id == Customer.id
        ).where(
            and_(
                Facility.is_deleted == False,
                Customer.is_deleted == False
            )
        )
        
        # Apply filters
        filters = []
        
        if customer_id:
            filters.append(Facility.customer_id == customer_id)
        
        if facility_type:
            filters.append(Facility.facility_type == facility_type)
        
        if status:
            filters.append(Facility.status == status)
        
        if search:
            search_filter = f"%{search.strip()}%"
            filters.append(Facility.name.ilike(search_filter))
        
        if filters:
            filter_condition = and_(*filters)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sorting
        sort_column = getattr(Facility, sort_by, Facility.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        rows = result.all()
        
        # Build response
        facility_responses = []
        for facility, customer_name in rows:
            facility_dict = facility.__dict__.copy()
            facility_dict['customer_name'] = customer_name
            facility_responses.append(facility_dict)
        
        return {
            "items": facility_responses,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve facilities: {str(e)}"
        )


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    """Get facility details by ID"""
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
        
        return FacilityResponse.from_orm(facility)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve facility: {str(e)}"
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
        
        # Update facility fields
        update_data = facility_data.model_dump(exclude_unset=True)
        # Remove amount field if present since it doesn't exist in database
        if 'amount' in update_data:
            del update_data['amount']
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
    # Removed amount_from and amount_to parameters since amount column doesn't exist
    # amount_from: Optional[float] = Query(None, description="Minimum amount"),
    # amount_to: Optional[float] = Query(None, description="Maximum amount"),
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
        
        # Removed amount filters since amount column doesn't exist in database
        # if amount_from is not None:
        #     conditions.append(Facility.amount >= amount_from)
        
        # if amount_to is not None:
        #     conditions.append(Facility.amount <= amount_to)
        
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
        for facility, customer_name in rows:
            facility_dict = facility.__dict__.copy()
            facility_dict['customer_name'] = customer_name
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