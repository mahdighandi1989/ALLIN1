"""
Customers API
API مدیریت مشتریان
"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, TokenData, require_permission
from app.core.database import get_db
from app.models.customer import Customer, AccountType, CustomerStatus

router = APIRouter()


# Schemas
class CustomerCreate(BaseModel):
    account_no: str
    customer_name: str
    branch: Optional[str] = None
    account_type: str = "retail"
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    branch: Optional[str] = None
    account_type: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    account_no: str
    customer_name: str
    branch: Optional[str]
    account_type: str
    status: str
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


def customer_to_dict(c: Customer) -> dict:
    return {
        "id": c.id,
        "account_no": c.account_no,
        "customer_name": c.customer_name,
        "branch": c.branch,
        "account_type": c.account_type.value if hasattr(c.account_type, 'value') else str(c.account_type),
        "status": c.status.value if hasattr(c.status, 'value') else str(c.status),
        "email": c.email,
        "phone": c.phone,
        "mobile": c.mobile,
        "address": c.address,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("/")
async def list_customers(
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    status: Optional[str] = None,
    branch: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List customers with pagination and filters"""
    query = select(Customer).where(Customer.is_deleted == False)

    # Filters
    if search:
        query = query.where(
            or_(
                Customer.customer_name.ilike(f"%{search}%"),
                Customer.account_no.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%")
            )
        )

    if account_type:
        try:
            query = query.where(Customer.account_type == AccountType(account_type))
        except ValueError:
            pass

    if status:
        try:
            query = query.where(Customer.status == CustomerStatus(status))
        except ValueError:
            pass

    if branch:
        query = query.where(Customer.branch == branch)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Customer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    customers = result.scalars().all()

    return {
        "items": [customer_to_dict(c) for c in customers],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.post("/")
async def create_customer(
    data: CustomerCreate,
    current_user: TokenData = Depends(require_permission("write:customers")),
    db: AsyncSession = Depends(get_db)
):
    """Create new customer"""
    # Check account_no unique
    result = await db.execute(
        select(Customer).where(Customer.account_no == data.account_no)
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Account number already exists")

    customer = Customer(
        account_no=data.account_no,
        customer_name=data.customer_name,
        branch=data.branch,
        account_type=AccountType(data.account_type) if data.account_type else AccountType.RETAIL,
        email=data.email,
        phone=data.phone,
        mobile=data.mobile,
        address=data.address,
        notes=data.notes,
        status=CustomerStatus.ACTIVE,
        created_by=current_user.user_id
    )

    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return customer_to_dict(customer)


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer by ID"""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.is_deleted == False
        )
    )
    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer_to_dict(customer)


@router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    current_user: TokenData = Depends(require_permission("write:customers")),
    db: AsyncSession = Depends(get_db)
):
    """Update customer"""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.is_deleted == False
        )
    )
    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "account_type":
                value = AccountType(value)
            elif field == "status":
                value = CustomerStatus(value)
            setattr(customer, field, value)

    customer.updated_by = current_user.user_id
    await db.commit()
    await db.refresh(customer)

    return customer_to_dict(customer)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: TokenData = Depends(require_permission("delete:customers")),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete customer"""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.is_deleted == False
        )
    )
    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.is_deleted = True
    customer.deleted_by = current_user.user_id
    await db.commit()

    return {"message": "Customer deleted successfully"}


@router.get("/stats/summary")
async def get_customer_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer statistics"""
    # Total customers
    total = (await db.execute(
        select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
    )).scalar() or 0

    # By type
    corporate = (await db.execute(
        select(func.count()).select_from(Customer).where(
            Customer.is_deleted == False,
            Customer.account_type == AccountType.CORPORATE
        )
    )).scalar() or 0

    retail = (await db.execute(
        select(func.count()).select_from(Customer).where(
            Customer.is_deleted == False,
            Customer.account_type == AccountType.RETAIL
        )
    )).scalar() or 0

    # By status
    active = (await db.execute(
        select(func.count()).select_from(Customer).where(
            Customer.is_deleted == False,
            Customer.status == CustomerStatus.ACTIVE
        )
    )).scalar() or 0

    return {
        "total": total,
        "by_type": {"corporate": corporate, "retail": retail},
        "by_status": {"active": active, "inactive": total - active}
    }
