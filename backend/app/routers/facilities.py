from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.models import Facility, Customer, FacilityType, FacilityStatus
from app.schemas.facility import (
    FacilityCreate, 
    FacilityUpdate, 
    FacilityResponse, 
    FacilityListResponse,
    FacilitySearchParams
)
from app.utils.id_generator import generate_facility_id

router = APIRouter()

@router.get("/", response_model=FacilityListResponse)
async def get_facilities(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[str] = None,
    facility_type: Optional[FacilityType] = None,
    status: Optional[FacilityStatus] = None,
    search: Optional[str] = None
):
    """Get paginated list of facilities with optional filtering"""
    # Build query
    query = select(Facility).where(Facility.is_deleted == False)
    
    if customer_id:
        query = query.where(Facility.customer_id == customer_id)
    if facility_type:
        query = query.where(Facility.facility_type == facility_type)
    if status:
        query = query.where(Facility.status == status)
    if search:
        query = query.where(or_(
            Facility.name.ilike(f"%{search}%"),
            Facility.id.ilike(f"%{search}%")
        ))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    facilities = result.scalars().all()
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return FacilityListResponse(
        items=facilities,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )

@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific facility by ID"""
    result = await db.execute(
        select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    )
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    return facility

@router.post("/", response_model=FacilityResponse, status_code=201)
async def create_facility(
    facility_data: FacilityCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create a new facility"""
    # Check if customer exists
    customer_result = await db.execute(
        select(Customer).where(Customer.id == facility_data.customer_id, Customer.is_deleted == False)
    )
    customer = customer_result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Generate facility ID
    facility_id = generate_facility_id()
    
    # Create facility
    facility = Facility(
        id=facility_id,
        **facility_data.model_dump()
    )
    
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    
    return facility

@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: str,
    facility_data: FacilityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing facility"""
    result = await db.execute(
        select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    )
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    # Update facility fields
    update_data = facility_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(facility, field, value)
    
    await db.commit()
    await db.refresh(facility)
    
    return facility

@router.delete("/{facility_id}", status_code=204)
async def delete_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Soft delete a facility"""
    result = await db.execute(
        select(Facility).where(Facility.id == facility_id, Facility.is_deleted == False)
    )
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    facility.is_deleted = True
    await db.commit()

@router.post("/search/advanced", response_model=FacilityListResponse)
async def search_facilities_advanced(
    search_params: FacilitySearchParams,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Advanced search for facilities"""
    query = select(Facility).where(Facility.is_deleted == False)
    
    if search_params.customer_id:
        query = query.where(Facility.customer_id == search_params.customer_id)
    if search_params.facility_type:
        query = query.where(Facility.facility_type == search_params.facility_type)
    if search_params.status:
        query = query.where(Facility.status == search_params.status)
    if search_params.search:
        query = query.where(or_(
            Facility.name.ilike(f"%{search_params.search}%"),
            Facility.id.ilike(f"%{search_params.search}%")
        ))
    if search_params.amount_from is not None:
        query = query.where(Facility.amount >= search_params.amount_from)
    if search_params.amount_to is not None:
        query = query.where(Facility.amount <= search_params.amount_to)
    if search_params.start_date_from:
        query = query.where(Facility.start_date >= search_params.start_date_from)
    if search_params.start_date_to:
        query = query.where(Facility.start_date <= search_params.start_date_to)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    facilities = result.scalars().all()
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return FacilityListResponse(
        items=facilities,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )