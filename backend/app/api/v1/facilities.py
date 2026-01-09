"""
Facilities API Routes
روت‌های مدیریت تسهیلات
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.core.security import get_current_user, TokenData, require_permission

router = APIRouter()


# ========== Schemas ==========
class FacilityBase(BaseModel):
    customer_id: str
    facility_type: str  # OD, Loan, LG, LC_Sight, LC_Usance, etc.
    approved_amount: float
    currency: str = "AED"
    sanction_date: Optional[date] = None
    maturity_date: Optional[date] = None
    interest_rate: Optional[float] = None


class FacilityCreate(FacilityBase):
    pass


class FacilityUpdate(BaseModel):
    facility_type: Optional[str] = None
    approved_amount: Optional[float] = None
    utilized_amount: Optional[float] = None
    status: Optional[str] = None
    maturity_date: Optional[date] = None
    interest_rate: Optional[float] = None
    notes: Optional[str] = None


class FacilityResponse(FacilityBase):
    id: str
    utilized_amount: float
    outstanding_amount: float
    available_amount: float
    status: str
    utilization_percentage: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class GuarantorCreate(BaseModel):
    guarantor_name: str
    relationship_type: Optional[str] = None
    passport_no: Optional[str] = None
    emirates_id: Optional[str] = None
    phone: Optional[str] = None
    guarantee_amount: Optional[float] = None


class ChequeCreate(BaseModel):
    cheque_no: str
    bank_name: Optional[str] = None
    amount: float
    cheque_date: Optional[date] = None


# ========== Routes ==========
@router.get("/")
async def list_facilities(
    customer_id: Optional[str] = None,
    facility_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """
    لیست تسهیلات با فیلتر
    """
    # Mock data
    facilities = [
        {
            "id": "FAC-001",
            "customer_id": "cust-001",
            "facility_type": "OD",
            "approved_amount": 2000000,
            "currency": "AED",
            "utilized_amount": 1500000,
            "outstanding_amount": 1500000,
            "available_amount": 500000,
            "status": "active",
            "utilization_percentage": 75,
            "sanction_date": "2024-01-15",
            "maturity_date": "2025-01-14",
            "interest_rate": 5.5,
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-06-01T14:30:00"
        },
        {
            "id": "FAC-002",
            "customer_id": "cust-001",
            "facility_type": "Loan",
            "approved_amount": 3000000,
            "currency": "AED",
            "utilized_amount": 3000000,
            "outstanding_amount": 1700000,
            "available_amount": 0,
            "status": "active",
            "utilization_percentage": 100,
            "sanction_date": "2024-03-01",
            "maturity_date": "2027-02-28",
            "interest_rate": 6.0,
            "created_at": "2024-03-01T09:00:00",
            "updated_at": "2024-07-15T16:20:00"
        }
    ]

    # Apply filters
    if customer_id:
        facilities = [f for f in facilities if f["customer_id"] == customer_id]

    if facility_type:
        facilities = [f for f in facilities if f["facility_type"] == facility_type]

    if status:
        facilities = [f for f in facilities if f["status"] == status]

    total = len(facilities)
    start = (page - 1) * page_size
    items = facilities[start:start + page_size]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=FacilityResponse)
async def create_facility(
    facility: FacilityCreate,
    current_user: TokenData = Depends(require_permission("write:facilities"))
):
    """
    ایجاد تسهیلات جدید
    """
    from datetime import datetime

    new_facility = {
        "id": f"FAC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        **facility.model_dump(),
        "utilized_amount": 0,
        "outstanding_amount": 0,
        "available_amount": facility.approved_amount,
        "status": "active",
        "utilization_percentage": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    return FacilityResponse(**new_facility)


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت جزئیات تسهیلات
    """
    facility = {
        "id": facility_id,
        "customer_id": "cust-001",
        "facility_type": "OD",
        "approved_amount": 2000000,
        "currency": "AED",
        "utilized_amount": 1500000,
        "outstanding_amount": 1500000,
        "available_amount": 500000,
        "status": "active",
        "utilization_percentage": 75,
        "sanction_date": "2024-01-15",
        "maturity_date": "2025-01-14",
        "interest_rate": 5.5,
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-06-01T14:30:00"
    }

    return FacilityResponse(**facility)


@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: str,
    facility: FacilityUpdate,
    current_user: TokenData = Depends(require_permission("write:facilities"))
):
    """
    بروزرسانی تسهیلات
    """
    from datetime import datetime

    # در عمل از دیتابیس بخوانید و بروزرسانی کنید
    updated = {
        "id": facility_id,
        "customer_id": "cust-001",
        "facility_type": facility.facility_type or "OD",
        "approved_amount": facility.approved_amount or 2000000,
        "currency": "AED",
        "utilized_amount": facility.utilized_amount or 1500000,
        "outstanding_amount": 1500000,
        "available_amount": 500000,
        "status": facility.status or "active",
        "utilization_percentage": 75,
        "sanction_date": "2024-01-15",
        "maturity_date": str(facility.maturity_date) if facility.maturity_date else "2025-01-14",
        "interest_rate": facility.interest_rate or 5.5,
        "created_at": "2024-01-15T10:00:00",
        "updated_at": datetime.utcnow().isoformat()
    }

    return FacilityResponse(**updated)


@router.delete("/{facility_id}")
async def delete_facility(
    facility_id: str,
    cascade: bool = False,
    current_user: TokenData = Depends(require_permission("delete:facilities"))
):
    """
    حذف تسهیلات
    cascade: حذف تمام داده‌های وابسته
    """
    return {"message": f"Facility {facility_id} deleted successfully", "cascade": cascade}


@router.get("/{facility_id}/guarantors")
async def get_facility_guarantors(
    facility_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت ضامن‌های تسهیلات
    """
    guarantors = [
        {
            "id": "GNT-001",
            "facility_id": facility_id,
            "guarantor_name": "Ali Mohammed",
            "relationship_type": "Director",
            "passport_no": "AB1234567",
            "emirates_id": "784-1234-5678901-2",
            "guarantee_amount": 2000000,
            "cheques": [
                {"cheque_no": "001234", "amount": 500000, "bank": "Emirates NBD"},
                {"cheque_no": "001235", "amount": 500000, "bank": "Emirates NBD"}
            ]
        }
    ]

    return {"items": guarantors, "total": len(guarantors)}


@router.post("/{facility_id}/guarantors")
async def add_guarantor(
    facility_id: str,
    guarantor: GuarantorCreate,
    current_user: TokenData = Depends(require_permission("write:facilities"))
):
    """
    افزودن ضامن به تسهیلات
    """
    from datetime import datetime

    new_guarantor = {
        "id": f"GNT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "facility_id": facility_id,
        **guarantor.model_dump(),
        "cheques": [],
        "created_at": datetime.utcnow().isoformat()
    }

    return new_guarantor


@router.post("/{facility_id}/guarantors/{guarantor_id}/cheques")
async def add_cheque(
    facility_id: str,
    guarantor_id: str,
    cheque: ChequeCreate,
    current_user: TokenData = Depends(require_permission("write:facilities"))
):
    """
    افزودن چک ضمانت
    """
    from datetime import datetime

    new_cheque = {
        "id": f"CHQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "guarantor_id": guarantor_id,
        **cheque.model_dump(),
        "status": "held",
        "created_at": datetime.utcnow().isoformat()
    }

    return new_cheque


@router.get("/types/list")
async def get_facility_types(
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت لیست انواع تسهیلات
    """
    return {
        "types": [
            {"code": "OD", "name": "Overdraft", "name_fa": "اضافه برداشت"},
            {"code": "Loan", "name": "Term Loan", "name_fa": "وام"},
            {"code": "ChqDisc", "name": "Cheque Discount", "name_fa": "تنزیل چک"},
            {"code": "LG", "name": "Letter of Guarantee", "name_fa": "ضمانت‌نامه"},
            {"code": "TR", "name": "Trust Receipt", "name_fa": "حواله"},
            {"code": "LC_Sight", "name": "LC Sight", "name_fa": "اعتبار اسنادی دیداری"},
            {"code": "LC_Usance", "name": "LC Usance", "name_fa": "اعتبار اسنادی یوزانس"},
            {"code": "LoG", "name": "Loan on Gold", "name_fa": "وام طلا"},
        ]
    }
