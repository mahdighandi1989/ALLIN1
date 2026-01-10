"""
Customers API Routes
روت‌های مدیریت مشتریان - با عملیات واقعی دیتابیس
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, TokenData, require_permission
from app.core.database import get_db
from app.models.customer import Customer, CustomerProfile, AccountType, CustomerStatus
from app.models.facility import Facility
from app.models.guarantor import Guarantor
from app.models.property import Property
from app.models.deposit import Deposit

router = APIRouter()


# ========== Schemas ==========
class CustomerBase(BaseModel):
    account_no: str
    customer_name: str
    customer_name_ar: Optional[str] = None
    account_type: str = "retail"
    branch: Optional[str] = None
    relationship_manager: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_name_ar: Optional[str] = None
    account_type: Optional[str] = None
    branch: Optional[str] = None
    relationship_manager: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    account_no: str
    customer_name: str
    customer_name_ar: Optional[str] = None
    account_type: str
    branch: Optional[str] = None
    relationship_manager: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    status: str
    profile_completeness: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CustomerProfileSchema(BaseModel):
    """پروفایل جامع مشتری"""
    trade_license_no: Optional[str] = None
    trade_license_expiry: Optional[date] = None
    passport_no: Optional[str] = None
    passport_expiry: Optional[date] = None
    nationality: Optional[str] = None
    emirates_id: Optional[str] = None
    emirates_id_expiry: Optional[date] = None
    visa_no: Optional[str] = None
    visa_expiry: Optional[date] = None
    annual_turnover: Optional[float] = None
    net_worth: Optional[float] = None
    custom_fields: Optional[dict] = None


class CustomerSummary(BaseModel):
    """خلاصه مشتری"""
    total_facilities: int
    total_facility_amount: float
    total_outstanding: float
    guarantors_count: int
    properties_count: int
    deposits_count: int
    kyc_status: str
    expiring_documents: List[dict]


class CustomerListResponse(BaseModel):
    """پاسخ لیست مشتریان"""
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ========== Helper Functions ==========
def customer_to_response(customer: Customer) -> CustomerResponse:
    """Convert Customer model to response schema"""
    return CustomerResponse(
        id=customer.id,
        account_no=customer.account_no,
        customer_name=customer.customer_name,
        customer_name_ar=customer.customer_name_ar,
        account_type=customer.account_type.value if hasattr(customer.account_type, 'value') else str(customer.account_type),
        branch=customer.branch,
        relationship_manager=customer.relationship_manager,
        phone=customer.phone,
        mobile=customer.mobile,
        email=customer.email,
        address=customer.address,
        notes=customer.notes,
        status=customer.status.value if hasattr(customer.status, 'value') else str(customer.status),
        profile_completeness=customer.profile_completeness or 0,
        created_at=customer.created_at.isoformat() if customer.created_at else datetime.utcnow().isoformat(),
        updated_at=customer.updated_at.isoformat() if customer.updated_at else datetime.utcnow().isoformat()
    )


# ========== Routes ==========
@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    branch: Optional[str] = None,
    status: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    لیست مشتریان با فیلتر و صفحه‌بندی
    """
    # Build query
    query = select(Customer).where(Customer.is_deleted == False)

    # Apply filters
    if search:
        search_filter = or_(
            Customer.account_no.ilike(f"%{search}%"),
            Customer.customer_name.ilike(f"%{search}%"),
            Customer.customer_name_ar.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%"),
            Customer.mobile.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    if account_type:
        try:
            acc_type = AccountType(account_type)
            query = query.where(Customer.account_type == acc_type)
        except ValueError:
            pass

    if branch:
        query = query.where(Customer.branch == branch)

    if status:
        try:
            cust_status = CustomerStatus(status)
            query = query.where(Customer.status == cust_status)
        except ValueError:
            pass

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Customer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    customers = result.scalars().all()

    # Convert to response
    items = [customer_to_response(c) for c in customers]

    return CustomerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 1
    )


@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    current_user: TokenData = Depends(require_permission("write:customers")),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد مشتری جدید
    """
    # Check if account_no already exists
    existing = await db.execute(
        select(Customer).where(Customer.account_no == customer.account_no)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Customer with account number {customer.account_no} already exists"
        )

    # Create new customer
    try:
        account_type = AccountType(customer.account_type)
    except ValueError:
        account_type = AccountType.RETAIL

    new_customer = Customer(
        account_no=customer.account_no,
        customer_name=customer.customer_name,
        customer_name_ar=customer.customer_name_ar,
        account_type=account_type,
        branch=customer.branch,
        relationship_manager=customer.relationship_manager,
        phone=customer.phone,
        mobile=customer.mobile,
        email=customer.email,
        address=customer.address,
        notes=customer.notes,
        status=CustomerStatus.ACTIVE,
        profile_completeness=20,
        created_by=current_user.user_id
    )

    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    return customer_to_response(new_customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت اطلاعات یک مشتری
    """
    result = await db.execute(
        select(Customer).where(
            and_(Customer.id == customer_id, Customer.is_deleted == False)
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer_to_response(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    current_user: TokenData = Depends(require_permission("write:customers")),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی مشتری
    """
    result = await db.execute(
        select(Customer).where(
            and_(Customer.id == customer_id, Customer.is_deleted == False)
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Update fields
    update_data = customer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "account_type":
                try:
                    value = AccountType(value)
                except ValueError:
                    continue
            setattr(customer, field, value)

    customer.updated_by = current_user.user_id
    await db.commit()
    await db.refresh(customer)

    return customer_to_response(customer)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: TokenData = Depends(require_permission("delete:customers")),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف مشتری (soft delete)
    """
    result = await db.execute(
        select(Customer).where(
            and_(Customer.id == customer_id, Customer.is_deleted == False)
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Soft delete
    customer.is_deleted = True
    customer.deleted_at = datetime.utcnow()
    customer.deleted_by = current_user.user_id
    await db.commit()

    return {"message": f"Customer {customer_id} deleted successfully", "success": True}


@router.get("/{customer_id}/profile", response_model=CustomerProfileSchema)
async def get_customer_profile(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت پروفایل جامع مشتری
    """
    result = await db.execute(
        select(Customer).options(selectinload(Customer.profile)).where(
            and_(Customer.id == customer_id, Customer.is_deleted == False)
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    profile = customer.profile
    if not profile:
        # Return empty profile
        return CustomerProfileSchema()

    return CustomerProfileSchema(
        trade_license_no=profile.trade_license_no,
        trade_license_expiry=profile.trade_license_expiry_date,
        passport_no=profile.passport_no,
        passport_expiry=profile.passport_expiry_date,
        nationality=profile.nationality,
        emirates_id=profile.emirates_id_no,
        emirates_id_expiry=profile.emirates_id_expiry_date,
        visa_no=profile.visa_no,
        visa_expiry=profile.visa_expiry_date,
        annual_turnover=float(profile.annual_turnover) if profile.annual_turnover else None,
        net_worth=float(profile.net_worth) if profile.net_worth else None,
        custom_fields=profile.custom_data
    )


@router.put("/{customer_id}/profile", response_model=CustomerProfileSchema)
async def update_customer_profile(
    customer_id: str,
    profile_data: CustomerProfileSchema,
    current_user: TokenData = Depends(require_permission("write:customers")),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی پروفایل مشتری
    """
    result = await db.execute(
        select(Customer).options(selectinload(Customer.profile)).where(
            and_(Customer.id == customer_id, Customer.is_deleted == False)
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    profile = customer.profile
    if not profile:
        # Create new profile
        profile = CustomerProfile(customer_id=customer_id)
        db.add(profile)

    # Update profile fields
    if profile_data.trade_license_no is not None:
        profile.trade_license_no = profile_data.trade_license_no
    if profile_data.trade_license_expiry is not None:
        profile.trade_license_expiry_date = profile_data.trade_license_expiry
    if profile_data.passport_no is not None:
        profile.passport_no = profile_data.passport_no
    if profile_data.passport_expiry is not None:
        profile.passport_expiry_date = profile_data.passport_expiry
    if profile_data.nationality is not None:
        profile.nationality = profile_data.nationality
    if profile_data.emirates_id is not None:
        profile.emirates_id_no = profile_data.emirates_id
    if profile_data.emirates_id_expiry is not None:
        profile.emirates_id_expiry_date = profile_data.emirates_id_expiry
    if profile_data.visa_no is not None:
        profile.visa_no = profile_data.visa_no
    if profile_data.visa_expiry is not None:
        profile.visa_expiry_date = profile_data.visa_expiry
    if profile_data.annual_turnover is not None:
        profile.annual_turnover = profile_data.annual_turnover
    if profile_data.net_worth is not None:
        profile.net_worth = profile_data.net_worth
    if profile_data.custom_fields is not None:
        profile.custom_data = profile_data.custom_fields

    profile.updated_by = current_user.user_id

    # Update customer profile completeness
    customer.profile_completeness = profile.calculate_completeness()

    await db.commit()
    await db.refresh(profile)

    return profile_data


@router.get("/{customer_id}/summary", response_model=CustomerSummary)
async def get_customer_summary(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت خلاصه مشتری
    """
    # Check customer exists
    result = await db.execute(
        select(Customer).options(selectinload(Customer.profile)).where(
            and_(Customer.id == customer_id, Customer.is_deleted == False)
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Get facilities stats
    facilities_result = await db.execute(
        select(
            func.count(Facility.id).label('count'),
            func.coalesce(func.sum(Facility.approved_amount), 0).label('total_amount'),
            func.coalesce(func.sum(Facility.outstanding_amount), 0).label('outstanding')
        ).where(
            and_(Facility.customer_id == customer_id, Facility.is_deleted == False)
        )
    )
    facilities_stats = facilities_result.one()

    # Get guarantors count
    guarantors_result = await db.execute(
        select(func.count(Guarantor.id)).where(
            and_(Guarantor.customer_id == customer_id, Guarantor.is_deleted == False)
        )
    )
    guarantors_count = guarantors_result.scalar() or 0

    # Get properties count
    properties_result = await db.execute(
        select(func.count(Property.id)).where(
            and_(Property.customer_id == customer_id, Property.is_deleted == False)
        )
    )
    properties_count = properties_result.scalar() or 0

    # Get deposits count
    deposits_result = await db.execute(
        select(func.count(Deposit.id)).where(
            and_(Deposit.customer_id == customer_id, Deposit.is_deleted == False)
        )
    )
    deposits_count = deposits_result.scalar() or 0

    # Get expiring documents from profile
    expiring_documents = []
    if customer.profile:
        expiring_documents = customer.profile.get_expiring_documents(days=90)

    return CustomerSummary(
        total_facilities=facilities_stats.count or 0,
        total_facility_amount=float(facilities_stats.total_amount or 0),
        total_outstanding=float(facilities_stats.outstanding or 0),
        guarantors_count=guarantors_count,
        properties_count=properties_count,
        deposits_count=deposits_count,
        kyc_status="complete" if customer.profile_completeness >= 70 else "incomplete",
        expiring_documents=[{
            "document": doc["document"],
            "expiry_date": doc["expiry_date"].isoformat() if hasattr(doc["expiry_date"], 'isoformat') else str(doc["expiry_date"]),
            "days_remaining": doc["days_remaining"]
        } for doc in expiring_documents]
    )


@router.get("/{customer_id}/facilities")
async def get_customer_facilities(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت لیست تسهیلات مشتری
    """
    result = await db.execute(
        select(Facility).where(
            and_(Facility.customer_id == customer_id, Facility.is_deleted == False)
        ).order_by(Facility.created_at.desc())
    )
    facilities = result.scalars().all()

    items = [{
        "id": f.id,
        "facility_type": f.facility_type.value if hasattr(f.facility_type, 'value') else str(f.facility_type),
        "approved_amount": float(f.approved_amount) if f.approved_amount else 0,
        "utilized_amount": float(f.utilized_amount) if f.utilized_amount else 0,
        "outstanding_amount": float(f.outstanding_amount) if f.outstanding_amount else 0,
        "status": f.status.value if hasattr(f.status, 'value') else str(f.status),
        "maturity_date": f.maturity_date.isoformat() if f.maturity_date else None
    } for f in facilities]

    return {"items": items, "total": len(items)}


@router.get("/{customer_id}/guarantors")
async def get_customer_guarantors(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت لیست ضامن‌های مشتری
    """
    result = await db.execute(
        select(Guarantor).where(
            and_(Guarantor.customer_id == customer_id, Guarantor.is_deleted == False)
        )
    )
    guarantors = result.scalars().all()

    items = [{
        "id": g.id,
        "guarantor_name": g.guarantor_name,
        "relationship": g.relationship,
        "guarantee_amount": float(g.guarantee_amount) if g.guarantee_amount else 0,
        "cheques_count": len(g.cheques) if g.cheques else 0
    } for g in guarantors]

    return {"items": items, "total": len(items)}


@router.get("/{customer_id}/properties")
async def get_customer_properties(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت لیست املاک مشتری
    """
    result = await db.execute(
        select(Property).where(
            and_(Property.customer_id == customer_id, Property.is_deleted == False)
        )
    )
    properties = result.scalars().all()

    items = [{
        "id": p.id,
        "location": p.location.value if hasattr(p.location, 'value') else str(p.location),
        "property_type": p.property_type.value if hasattr(p.property_type, 'value') else str(p.property_type),
        "current_value": float(p.current_value) if p.current_value else 0,
        "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
        "address": p.address
    } for p in properties]

    return {"items": items, "total": len(items)}


@router.get("/{customer_id}/deposits")
async def get_customer_deposits(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت لیست سپرده‌های مشتری
    """
    result = await db.execute(
        select(Deposit).where(
            and_(Deposit.customer_id == customer_id, Deposit.is_deleted == False)
        )
    )
    deposits = result.scalars().all()

    items = [{
        "id": d.id,
        "deposit_type": d.deposit_type.value if hasattr(d.deposit_type, 'value') else str(d.deposit_type),
        "principal_amount": float(d.principal_amount) if d.principal_amount else 0,
        "maturity_date": d.maturity_date.isoformat() if d.maturity_date else None,
        "is_under_lien": d.is_under_lien
    } for d in deposits]

    return {"items": items, "total": len(items)}


@router.post("/{customer_id}/attachments")
async def upload_attachment(
    customer_id: str,
    file: UploadFile = File(...),
    category: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("write:customers")),
    db: AsyncSession = Depends(get_db)
):
    """
    آپلود پیوست برای مشتری
    """
    # Check customer exists
    result = await db.execute(
        select(Customer).where(
            and_(Customer.id == customer_id, Customer.is_deleted == False)
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    from app.services.file_service import file_service

    content = await file.read()
    result = await file_service.save_file(
        content=content,
        original_name=file.filename,
        customer_id=customer_id
    )

    return result


@router.get("/{customer_id}/attachments")
async def get_customer_attachments(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت لیست پیوست‌های مشتری
    """
    from app.services.file_service import file_service

    files = await file_service.list_files(
        subfolder="attachments",
        customer_id=customer_id
    )

    return {"items": files, "total": len(files)}
