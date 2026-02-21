from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.schemas.facility import FacilityCreate, FacilityUpdate, FacilityResponse

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("/", response_model=List[FacilityResponse])
async def list_facilities(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    facility_type: Optional[FacilityType] = Query(None, description="Filter by facility type"),
    status: Optional[FacilityStatus] = Query(None, description="Filter by facility status"),
    search: Optional[str] = Query(None, description="Search term for facility name"),
):
    """
    Retrieve a list of facilities with optional filtering and pagination.
    """
    query = select(Facility).where(Facility.is_deleted == False)
    
    if customer_id:
        query = query.where(Facility.customer_id == customer_id)
    
    if facility_type:
        query = query.where(Facility.facility_type == facility_type)
    
    if status:
        query = query.where(Facility.status == status)
    
    if search:
        query = query.where(Facility.name.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    facilities = result.scalars().all()
    return facilities


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific facility by ID.
    """
    query = select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    result = await db.execute(query)
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID {facility_id} not found"
        )
    
    return facility


@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
async def create_facility(
    facility_data: FacilityCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new facility.
    """
    # Check if customer exists
    from app.models.customer import Customer
    customer_query = select(Customer).where(Customer.id == facility_data.customer_id, Customer.is_deleted == False)
    customer_result = await db.execute(customer_query)
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with ID {facility_data.customer_id} not found"
        )
    
    # Generate facility ID if not provided
    if not hasattr(facility_data, 'id') or not facility_data.id:
        from app.utils.id_generator import generate_facility_id
        facility_id = generate_facility_id()
        facility_dict = facility_data.dict()
        facility_dict['id'] = facility_id
        new_facility = Facility(**facility_dict)
    else:
        new_facility = Facility(**facility_data.dict())
    
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
    """
    Update an existing facility.
    """
    query = select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    result = await db.execute(query)
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID {facility_id} not found"
        )
    
    # Check if customer exists if customer_id is being updated
    if facility_data.customer_id and facility_data.customer_id != facility.customer_id:
        from app.models.customer import Customer
        customer_query = select(Customer).where(Customer.id == facility_data.customer_id, Customer.is_deleted == False)
        customer_result = await db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with ID {facility_data.customer_id} not found"
            )
    
    # Update facility attributes
    update_data = facility_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(facility, field, value)
    
    await db.commit()
    await db.refresh(facility)
    
    return facility


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facility(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a facility.
    """
    query = select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    result = await db.execute(query)
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID {facility_id} not found"
        )
    
    facility.is_deleted = True
    await db.commit()
    
    return None