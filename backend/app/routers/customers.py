"""Customers Router"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Customer, AccountType, CustomerStatus
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerList
from app.utils.security import get_current_user, TokenData

router = APIRouter(prefix="/api/customers", tags=["Customers"])


def customer_to_response(c: Customer) -> dict:
    return {
        "id": c.id,
        "account_no": c.account_no,
        "name": c.name,
        "name_ar": c.name_ar,
        "account_type": c.account_type.value if c.account_type else "retail",
        "status": c.status.value if c.status else "active",
        "email": c.email,
        "phone": c.phone,
        "mobile": c.mobile,
        "address": c.address,
        "branch": c.branch,
        "relationship_manager": c.relationship_manager,
        "notes": c.notes,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


@router.get("", response_model=CustomerList)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = None,
    status: str = None,
    account_type: str = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List customers with pagination"""
    query = select(Customer).where(Customer.is_deleted == False)

    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%") |
            Customer.account_no.ilike(f"%{search}%")
        )

    if status:
        try:
            query = query.where(Customer.status == CustomerStatus(status))
        except ValueError:
            pass

    if account_type:
        try:
            query = query.where(Customer.account_type == AccountType(account_type))
        except ValueError:
            pass

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.order_by(Customer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    customers = result.scalars().all()

    return CustomerList(
        items=[customer_to_response(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer by ID"""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    )
    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer_to_response(customer)


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new customer"""
    # Check account_no
    result = await db.execute(select(Customer).where(Customer.account_no == data.account_no))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Account number already exists")

    customer = Customer(
        account_no=data.account_no,
        name=data.name,
        name_ar=data.name_ar,
        account_type=AccountType(data.account_type) if data.account_type else AccountType.RETAIL,
        email=data.email,
        phone=data.phone,
        mobile=data.mobile,
        address=data.address,
        branch=data.branch,
        relationship_manager=data.relationship_manager,
        notes=data.notes
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return customer_to_response(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update customer"""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    )
    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "status":
                value = CustomerStatus(value)
            elif field == "account_type":
                value = AccountType(value)
            setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)

    return customer_to_response(customer)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete customer (soft delete)"""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    )
    customer = result.scalars().first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.is_deleted = True
    await db.commit()

    return {"message": "Customer deleted"}
