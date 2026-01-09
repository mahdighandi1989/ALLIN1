"""
Customers API Routes
روت‌های مدیریت مشتریان
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel, Field

from app.core.security import get_current_user, TokenData, require_permission

router = APIRouter()


# ========== Schemas ==========
class CustomerBase(BaseModel):
    account_no: str
    customer_name: str
    customer_name_ar: Optional[str] = None
    account_type: str = "retail"  # corporate, retail, sme
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


class CustomerResponse(CustomerBase):
    id: str
    status: str
    profile_completeness: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CustomerProfile(BaseModel):
    """پروفایل جامع مشتری"""
    # Trade License
    trade_license_no: Optional[str] = None
    trade_license_expiry: Optional[date] = None

    # Passport
    passport_no: Optional[str] = None
    passport_expiry: Optional[date] = None
    nationality: Optional[str] = None

    # Emirates ID
    emirates_id: Optional[str] = None
    emirates_id_expiry: Optional[date] = None

    # Visa
    visa_no: Optional[str] = None
    visa_expiry: Optional[date] = None

    # Financial
    annual_turnover: Optional[float] = None
    net_worth: Optional[float] = None

    # Additional
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


# ========== Routes ==========
@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    branch: Optional[str] = None,
    status: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    لیست مشتریان با فیلتر و صفحه‌بندی
    """
    # Mock data - در عمل از دیتابیس بخوانید
    customers = [
        {
            "id": "cust-001",
            "account_no": "123456",
            "customer_name": "ABC Trading LLC",
            "customer_name_ar": "شرکت ABC للتجارة",
            "account_type": "corporate",
            "branch": "Dubai Main",
            "relationship_manager": "John Doe",
            "phone": "+971-4-1234567",
            "mobile": "+971-50-1234567",
            "email": "info@abctrading.ae",
            "address": "Dubai, UAE",
            "notes": None,
            "status": "active",
            "profile_completeness": 85,
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-06-20T14:45:00"
        },
        {
            "id": "cust-002",
            "account_no": "789012",
            "customer_name": "Mohammad Ali",
            "customer_name_ar": "محمد علی",
            "account_type": "retail",
            "branch": "Abu Dhabi",
            "relationship_manager": "Jane Smith",
            "phone": None,
            "mobile": "+971-55-9876543",
            "email": "m.ali@email.com",
            "address": "Abu Dhabi, UAE",
            "notes": None,
            "status": "active",
            "profile_completeness": 72,
            "created_at": "2024-03-10T09:15:00",
            "updated_at": "2024-07-01T11:20:00"
        }
    ]

    # Apply filters
    if search:
        search_lower = search.lower()
        customers = [
            c for c in customers
            if search_lower in c["account_no"].lower()
            or search_lower in c["customer_name"].lower()
        ]

    if account_type:
        customers = [c for c in customers if c["account_type"] == account_type]

    if branch:
        customers = [c for c in customers if c.get("branch") == branch]

    if status:
        customers = [c for c in customers if c["status"] == status]

    # Pagination
    total = len(customers)
    start = (page - 1) * page_size
    end = start + page_size
    items = customers[start:end]

    return CustomerListResponse(
        items=[CustomerResponse(**c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    current_user: TokenData = Depends(require_permission("write:customers"))
):
    """
    ایجاد مشتری جدید
    """
    from datetime import datetime

    # در عمل در دیتابیس ذخیره کنید
    new_customer = {
        "id": f"cust-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        **customer.model_dump(),
        "status": "active",
        "profile_completeness": 20,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    return CustomerResponse(**new_customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت اطلاعات یک مشتری
    """
    # Mock data
    customer = {
        "id": customer_id,
        "account_no": "123456",
        "customer_name": "ABC Trading LLC",
        "customer_name_ar": "شرکت ABC للتجارة",
        "account_type": "corporate",
        "branch": "Dubai Main",
        "relationship_manager": "John Doe",
        "phone": "+971-4-1234567",
        "mobile": "+971-50-1234567",
        "email": "info@abctrading.ae",
        "address": "Dubai, UAE",
        "notes": None,
        "status": "active",
        "profile_completeness": 85,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-06-20T14:45:00"
    }

    return CustomerResponse(**customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    current_user: TokenData = Depends(require_permission("write:customers"))
):
    """
    بروزرسانی مشتری
    """
    from datetime import datetime

    # در عمل از دیتابیس بخوانید و بروزرسانی کنید
    updated = {
        "id": customer_id,
        "account_no": "123456",
        "customer_name": customer.customer_name or "ABC Trading LLC",
        "customer_name_ar": customer.customer_name_ar,
        "account_type": customer.account_type or "corporate",
        "branch": customer.branch or "Dubai Main",
        "relationship_manager": customer.relationship_manager,
        "phone": customer.phone,
        "mobile": customer.mobile,
        "email": customer.email,
        "address": customer.address,
        "notes": customer.notes,
        "status": "active",
        "profile_completeness": 85,
        "created_at": "2024-01-15T10:30:00",
        "updated_at": datetime.utcnow().isoformat()
    }

    return CustomerResponse(**updated)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: TokenData = Depends(require_permission("delete:customers"))
):
    """
    حذف مشتری (soft delete)
    """
    # در عمل soft delete انجام دهید
    return {"message": f"Customer {customer_id} deleted successfully"}


@router.get("/{customer_id}/profile", response_model=CustomerProfile)
async def get_customer_profile(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت پروفایل جامع مشتری
    """
    # Mock data
    profile = {
        "trade_license_no": "TL-12345",
        "trade_license_expiry": "2025-06-30",
        "passport_no": "AB1234567",
        "passport_expiry": "2028-12-15",
        "nationality": "UAE",
        "emirates_id": "784-1234-5678901-2",
        "emirates_id_expiry": "2026-03-20",
        "visa_no": "V-987654",
        "visa_expiry": "2025-08-10",
        "annual_turnover": 5000000.00,
        "net_worth": 2500000.00,
        "custom_fields": {"industry": "Trading", "years_in_business": 10}
    }

    return CustomerProfile(**profile)


@router.put("/{customer_id}/profile", response_model=CustomerProfile)
async def update_customer_profile(
    customer_id: str,
    profile: CustomerProfile,
    current_user: TokenData = Depends(require_permission("write:customers"))
):
    """
    بروزرسانی پروفایل مشتری
    """
    # در عمل در دیتابیس بروزرسانی کنید
    return profile


@router.get("/{customer_id}/summary", response_model=CustomerSummary)
async def get_customer_summary(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت خلاصه مشتری
    """
    # Mock data
    summary = {
        "total_facilities": 3,
        "total_facility_amount": 5000000.00,
        "total_outstanding": 3200000.00,
        "guarantors_count": 2,
        "properties_count": 4,
        "deposits_count": 2,
        "kyc_status": "complete",
        "expiring_documents": [
            {"document": "Trade License", "expiry_date": "2025-06-30", "days_remaining": 172},
            {"document": "Visa", "expiry_date": "2025-08-10", "days_remaining": 213}
        ]
    }

    return CustomerSummary(**summary)


@router.get("/{customer_id}/facilities")
async def get_customer_facilities(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت لیست تسهیلات مشتری
    """
    # این endpoint به facilities router فرستاده می‌شود
    facilities = [
        {
            "id": "fac-001",
            "facility_type": "OD",
            "approved_amount": 2000000,
            "utilized_amount": 1500000,
            "status": "active"
        },
        {
            "id": "fac-002",
            "facility_type": "Loan",
            "approved_amount": 3000000,
            "utilized_amount": 1700000,
            "status": "active"
        }
    ]

    return {"items": facilities, "total": len(facilities)}


@router.get("/{customer_id}/guarantors")
async def get_customer_guarantors(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت لیست ضامن‌های مشتری
    """
    guarantors = [
        {
            "id": "gnt-001",
            "guarantor_name": "Ali Mohammed",
            "relationship": "Director",
            "guarantee_amount": 2000000,
            "cheques_count": 3
        }
    ]

    return {"items": guarantors, "total": len(guarantors)}


@router.get("/{customer_id}/properties")
async def get_customer_properties(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت لیست املاک مشتری
    """
    properties = [
        {
            "id": "prp-001",
            "location": "UAE",
            "property_type": "Villa",
            "current_value": 2500000,
            "status": "mortgaged"
        }
    ]

    return {"items": properties, "total": len(properties)}


@router.get("/{customer_id}/deposits")
async def get_customer_deposits(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت لیست سپرده‌های مشتری
    """
    deposits = [
        {
            "id": "dep-001",
            "deposit_type": "FD",
            "principal_amount": 500000,
            "maturity_date": "2025-12-31",
            "is_under_lien": True
        }
    ]

    return {"items": deposits, "total": len(deposits)}


@router.post("/{customer_id}/attachments")
async def upload_attachment(
    customer_id: str,
    file: UploadFile = File(...),
    category: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("write:customers"))
):
    """
    آپلود پیوست برای مشتری
    """
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
    current_user: TokenData = Depends(get_current_user)
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
