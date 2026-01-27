from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.database import get_db
from app.models.customers import Customer
from app.schemas.customers import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.auth import get_current_user
from app.models.users import User

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = None,
    national_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of customers with pagination and filtering.
    """
    query = select(Customer).where(Customer.deleted_at.is_(None))
    
    if name:
        query = query.where(Customer.name.ilike(f"%{name}%"))
    if national_id:
        query = query.where(Customer.national_id == national_id)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(Customer.created_at.desc())
    
    result = await db.execute(query)
    customers = result.scalars().all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get customer details by ID.
    """
    query = select(Customer).where(
        and_(
            Customer.id == customer_id,
            Customer.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new customer.
    """
    # Check if national_id already exists
    query = select(Customer).where(
        and_(
            Customer.national_id == customer_data.national_id,
            Customer.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    existing_customer = result.scalar_one_or_none()
    
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this national ID already exists"
        )
    
    # Create new customer
    customer_dict = customer_data.dict()
    customer_dict["created_by"] = current_user.id
    customer_dict["updated_by"] = current_user.id
    
    customer = Customer(**customer_dict)
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update customer information.
    """
    # Check if customer exists and is not deleted
    query = select(Customer).where(
        and_(
            Customer.id == customer_id,
            Customer.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Check if national_id is being changed and conflicts with existing customer
    if customer_data.national_id and customer_data.national_id != customer.national_id:
        conflict_query = select(Customer).where(
            and_(
                Customer.national_id == customer_data.national_id,
                Customer.id != customer_id,
                Customer.deleted_at.is_(None)
            )
        )
        conflict_result = await db.execute(conflict_query)
        conflicting_customer = conflict_result.scalar_one_or_none()
        
        if conflicting_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another customer with this national ID already exists"
            )
    
    # Update customer
    update_data = customer_data.dict(exclude_unset=True)
    update_data["updated_by"] = current_user.id
    
    stmt = (
        update(Customer)
        .where(Customer.id == customer_id)
        .values(**update_data)
    )
    await db.execute(stmt)
    await db.commit()
    
    # Get updated customer
    query = select(Customer).where(Customer.id == customer_id)
    result = await db.execute(query)
    updated_customer = result.scalar_one()
    
    return updated_customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a customer.
    """
    # Check if customer exists and is not already deleted
    query = select(Customer).where(
        and_(
            Customer.id == customer_id,
            Customer.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Soft delete customer
    from datetime import datetime
    stmt = (
        update(Customer)
        .where(Customer.id == customer_id)
        .values(
            deleted_at=datetime.utcnow(),
            updated_by=current_user.id,
            is_active=False
        )
    )
    await db.execute(stmt)
    await db.commit()