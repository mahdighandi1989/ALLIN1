from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility

router = APIRouter(prefix="/customers", tags=["customers"])


# Schemas
class CustomerBase(BaseModel):
    account_no: Optional[str] = None
    name: str
    account_type: Optional[str] = "retail"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    account_no: Optional[str] = None
    name: Optional[str] = None
    account_type: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: str
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(CustomerResponse):
    facilities: List[dict] = []
    
    @classmethod
    def from_customer_with_facilities(cls, customer: Customer, facilities: List[Facility]):
        customer_dict = customer.__dict__.copy()
        customer_dict['facilities'] = [
            {
                'id': f.id,
                'name': f.name,
                'amount': float(f.amount) if f.amount is not None else 0.0,
                'currency': f.currency,
                'status': f.status.value if f.status else None
            }
            for f in facilities
        ]
        return cls(**customer_dict)


# Endpoints
@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of customers with pagination and search"""
    try:
        query = select(Customer).where(Customer.is_deleted == False)
        
        if search:
            search_filter = and_(
                Customer.is_deleted == False,
                Customer.name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        query = query.offset(skip).limit(limit).order_by(Customer.created_at.desc())
        
        result = await db.execute(query)
        customers = result.scalars().all()
        
        return customers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching customers: {str(e)}"
        )


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific customer by ID with their facilities"""
    try:
        # Get customer
        customer_result = await db.execute(
            select(Customer).where(and_(Customer.id == customer_id, Customer.is_deleted == False))
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )
        
        # Get customer's facilities
        facilities_result = await db.execute(
            select(Facility).where(and_(Facility.customer_id == customer_id, Facility.is_deleted == False))
        )
        facilities = facilities_result.scalars().all()
        
        return CustomerDetailResponse.from_customer_with_facilities(customer, facilities)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching customer: {str(e)}"
        )


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(customer_data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    """Create a new customer"""
    try:
        # Check if account_no already exists
        if customer_data.account_no:
            existing_result = await db.execute(
                select(Customer).where(Customer.account_no == customer_data.account_no)
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Customer with account number {customer_data.account_no} already exists"
                )
        
        # Create new customer
        customer = Customer(**customer_data.model_dump(exclude_unset=True))
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer: {str(e)}"
        )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing customer"""
    try:
        # Get customer
        customer_result = await db.execute(
            select(Customer).where(and_(Customer.id == customer_id, Customer.is_deleted == False))
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )
        
        # Check account_no uniqueness if provided
        if customer_data.account_no and customer_data.account_no != customer.account_no:
            existing_result = await db.execute(
                select(Customer).where(and_(
                    Customer.account_no == customer_data.account_no,
                    Customer.id != customer_id
                ))
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Account number {customer_data.account_no} already exists"
                )
        
        # Update fields
        update_data = customer_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        await db.commit()
        await db.refresh(customer)
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating customer: {str(e)}"
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Soft delete a customer (set is_deleted = True)"""
    try:
        # Get customer
        customer_result = await db.execute(
            select(Customer).where(and_(Customer.id == customer_id, Customer.is_deleted == False))
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )
        
        # Soft delete
        customer.is_deleted = True
        await db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting customer: {str(e)}"
        )
