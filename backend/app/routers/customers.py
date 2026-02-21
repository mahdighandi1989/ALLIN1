from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for customer name"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
):
    """
    Retrieve a list of customers with optional filtering and pagination.
    """
    query = select(Customer).where(Customer.is_deleted == False)
    
    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))
    
    if account_type:
        query = query.where(Customer.account_type == account_type)
    
    if status:
        query = query.where(Customer.status == status)
    
    if branch:
        query = query.where(Customer.branch == branch)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    customers = result.scalars().all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific customer by ID.
    """
    query = select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    
    return customer


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new customer.
    """
    # Check if account_no already exists
    existing_query = select(Customer).where(Customer.account_no == customer_data.account_no)
    result = await db.execute(existing_query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with account number {customer_data.account_no} already exists"
        )
    
    new_customer = Customer(**customer_data.dict())
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    
    return new_customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing customer.
    """
    query = select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    
    # Check if account_no is being changed and conflicts
    if customer_data.account_no and customer_data.account_no != customer.account_no:
        existing_query = select(Customer).where(Customer.account_no == customer_data.account_no)
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with account number {customer_data.account_no} already exists"
            )
    
    # Update customer attributes
    update_data = customer_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    await db.commit()
    await db.refresh(customer)
    
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a customer (set is_deleted=True).
    """
    query = select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    
    customer.is_deleted = True
    await db.commit()

    return None
