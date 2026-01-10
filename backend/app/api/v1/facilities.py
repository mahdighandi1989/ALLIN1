"""
Facilities API Routes
روت‌های مدیریت تسهیلات - با عملیات واقعی دیتابیس
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, TokenData, require_permission
from app.core.database import get_db
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.guarantor import Guarantor, GuarantorCheque
from app.models.customer import Customer

router = APIRouter()


# ========== Schemas ==========
class FacilityBase(BaseModel):
    customer_id: str
    facility_type: str
    approved_amount: float
    currency: str = "AED"
    sanction_date: Optional[date] = None
    maturity_date: Optional[date] = None
    interest_rate: Optional[float] = None
    facility_name: Optional[str] = None
    notes: Optional[str] = None


class FacilityCreate(FacilityBase):
    pass


class FacilityUpdate(BaseModel):
    facility_type: Optional[str] = None
    approved_amount: Optional[float] = None
    utilized_amount: Optional[float] = None
    outstanding_amount: Optional[float] = None
    status: Optional[str] = None
    maturity_date: Optional[date] = None
    interest_rate: Optional[float] = None
    notes: Optional[str] = None


class FacilityResponse(BaseModel):
    id: str
    customer_id: str
    facility_type: str
    facility_name: Optional[str] = None
    approved_amount: float
    currency: str
    utilized_amount: float
    outstanding_amount: float
    available_amount: float
    status: str
    utilization_percentage: float
    sanction_date: Optional[str] = None
    maturity_date: Optional[str] = None
    interest_rate: Optional[float] = None
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


# ========== Helper Functions ==========
def facility_to_response(facility: Facility) -> FacilityResponse:
    """Convert Facility model to response schema"""
    approved = float(facility.approved_amount) if facility.approved_amount else 0
    utilized = float(facility.utilized_amount) if facility.utilized_amount else 0
    outstanding = float(facility.outstanding_amount) if facility.outstanding_amount else 0
    available = approved - utilized

    utilization_pct = (utilized / approved * 100) if approved > 0 else 0

    return FacilityResponse(
        id=facility.id,
        customer_id=facility.customer_id,
        facility_type=facility.facility_type.value if hasattr(facility.facility_type, 'value') else str(facility.facility_type),
        facility_name=facility.facility_name,
        approved_amount=approved,
        currency=facility.currency or "AED",
        utilized_amount=utilized,
        outstanding_amount=outstanding,
        available_amount=available,
        status=facility.status.value if hasattr(facility.status, 'value') else str(facility.status),
        utilization_percentage=round(utilization_pct, 2),
        sanction_date=facility.sanction_date.isoformat() if facility.sanction_date else None,
        maturity_date=facility.maturity_date.isoformat() if facility.maturity_date else None,
        interest_rate=float(facility.interest_rate) if facility.interest_rate else None,
        created_at=facility.created_at.isoformat() if facility.created_at else datetime.utcnow().isoformat(),
        updated_at=facility.updated_at.isoformat() if facility.updated_at else datetime.utcnow().isoformat()
    )


# ========== Routes ==========
@router.get("/")
async def list_facilities(
    customer_id: Optional[str] = None,
    facility_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    لیست تسهیلات با فیلتر
    """
    # Build query
    query = select(Facility).where(Facility.is_deleted == False)

    # Apply filters
    if customer_id:
        query = query.where(Facility.customer_id == customer_id)

    if facility_type:
        try:
            fac_type = FacilityType(facility_type)
            query = query.where(Facility.facility_type == fac_type)
        except ValueError:
            pass

    if status:
        try:
            fac_status = FacilityStatus(status)
            query = query.where(Facility.status == fac_status)
        except ValueError:
            pass

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Facility.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    facilities = result.scalars().all()

    items = [facility_to_response(f) for f in facilities]

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.post("/", response_model=FacilityResponse)
async def create_facility(
    facility: FacilityCreate,
    current_user: TokenData = Depends(require_permission("write:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد تسهیلات جدید
    """
    # Check customer exists
    customer_result = await db.execute(
        select(Customer).where(
            and_(Customer.id == facility.customer_id, Customer.is_deleted == False)
        )
    )
    if not customer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    # Parse facility type
    try:
        fac_type = FacilityType(facility.facility_type)
    except ValueError:
        fac_type = FacilityType.OTHER

    # Create new facility
    new_facility = Facility(
        customer_id=facility.customer_id,
        facility_type=fac_type,
        facility_name=facility.facility_name,
        approved_amount=facility.approved_amount,
        currency=facility.currency,
        utilized_amount=0,
        outstanding_amount=0,
        available_amount=facility.approved_amount,
        sanction_date=facility.sanction_date,
        maturity_date=facility.maturity_date,
        interest_rate=facility.interest_rate,
        status=FacilityStatus.ACTIVE,
        notes=facility.notes,
        created_by=current_user.user_id
    )

    db.add(new_facility)
    await db.commit()
    await db.refresh(new_facility)

    return facility_to_response(new_facility)


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت جزئیات تسهیلات
    """
    result = await db.execute(
        select(Facility).where(
            and_(Facility.id == facility_id, Facility.is_deleted == False)
        )
    )
    facility = result.scalar_one_or_none()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    return facility_to_response(facility)


@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: str,
    facility_update: FacilityUpdate,
    current_user: TokenData = Depends(require_permission("write:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی تسهیلات
    """
    result = await db.execute(
        select(Facility).where(
            and_(Facility.id == facility_id, Facility.is_deleted == False)
        )
    )
    facility = result.scalar_one_or_none()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    # Update fields
    update_data = facility_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "facility_type":
                try:
                    value = FacilityType(value)
                except ValueError:
                    continue
            elif field == "status":
                try:
                    value = FacilityStatus(value)
                except ValueError:
                    continue
            setattr(facility, field, value)

    # Recalculate available amount
    facility.calculate_available()
    facility.updated_by = current_user.user_id

    await db.commit()
    await db.refresh(facility)

    return facility_to_response(facility)


@router.delete("/{facility_id}")
async def delete_facility(
    facility_id: str,
    cascade: bool = False,
    current_user: TokenData = Depends(require_permission("delete:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف تسهیلات
    cascade: حذف تمام داده‌های وابسته
    """
    result = await db.execute(
        select(Facility).where(
            and_(Facility.id == facility_id, Facility.is_deleted == False)
        )
    )
    facility = result.scalar_one_or_none()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    # Soft delete
    facility.is_deleted = True
    facility.deleted_at = datetime.utcnow()
    facility.deleted_by = current_user.user_id

    if cascade:
        # Also soft delete related guarantors
        guarantors_result = await db.execute(
            select(Guarantor).where(Guarantor.facility_id == facility_id)
        )
        guarantors = guarantors_result.scalars().all()
        for g in guarantors:
            g.is_deleted = True
            g.deleted_at = datetime.utcnow()
            g.deleted_by = current_user.user_id

    await db.commit()

    return {"message": f"Facility {facility_id} deleted successfully", "cascade": cascade, "success": True}


@router.get("/{facility_id}/guarantors")
async def get_facility_guarantors(
    facility_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت ضامن‌های تسهیلات
    """
    result = await db.execute(
        select(Guarantor).options(selectinload(Guarantor.cheques)).where(
            and_(Guarantor.facility_id == facility_id, Guarantor.is_deleted == False)
        )
    )
    guarantors = result.scalars().all()

    items = [{
        "id": g.id,
        "facility_id": g.facility_id,
        "guarantor_name": g.guarantor_name,
        "relationship_type": g.relationship_type,
        "passport_no": g.passport_no,
        "emirates_id": g.emirates_id,
        "phone": g.phone,
        "guarantee_amount": float(g.guarantee_amount) if g.guarantee_amount else 0,
        "cheques": [{
            "id": c.id,
            "cheque_no": c.cheque_no,
            "amount": float(c.amount) if c.amount else 0,
            "bank": c.bank_name,
            "status": c.status
        } for c in g.cheques] if g.cheques else []
    } for g in guarantors]

    return {"items": items, "total": len(items)}


@router.post("/{facility_id}/guarantors")
async def add_guarantor(
    facility_id: str,
    guarantor: GuarantorCreate,
    current_user: TokenData = Depends(require_permission("write:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """
    افزودن ضامن به تسهیلات
    """
    # Check facility exists
    facility_result = await db.execute(
        select(Facility).where(
            and_(Facility.id == facility_id, Facility.is_deleted == False)
        )
    )
    facility = facility_result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    # Create guarantor
    new_guarantor = Guarantor(
        customer_id=facility.customer_id,
        facility_id=facility_id,
        guarantor_name=guarantor.guarantor_name,
        relationship_type=guarantor.relationship_type,
        passport_no=guarantor.passport_no,
        emirates_id=guarantor.emirates_id,
        phone=guarantor.phone,
        guarantee_amount=guarantor.guarantee_amount,
        created_by=current_user.user_id
    )

    db.add(new_guarantor)
    await db.commit()
    await db.refresh(new_guarantor)

    return {
        "id": new_guarantor.id,
        "facility_id": facility_id,
        "guarantor_name": new_guarantor.guarantor_name,
        "relationship_type": new_guarantor.relationship_type,
        "passport_no": new_guarantor.passport_no,
        "emirates_id": new_guarantor.emirates_id,
        "phone": new_guarantor.phone,
        "guarantee_amount": float(new_guarantor.guarantee_amount) if new_guarantor.guarantee_amount else 0,
        "cheques": [],
        "created_at": new_guarantor.created_at.isoformat() if new_guarantor.created_at else datetime.utcnow().isoformat()
    }


@router.delete("/{facility_id}/guarantors/{guarantor_id}")
async def delete_guarantor(
    facility_id: str,
    guarantor_id: str,
    current_user: TokenData = Depends(require_permission("delete:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف ضامن
    """
    result = await db.execute(
        select(Guarantor).where(
            and_(
                Guarantor.id == guarantor_id,
                Guarantor.facility_id == facility_id,
                Guarantor.is_deleted == False
            )
        )
    )
    guarantor = result.scalar_one_or_none()

    if not guarantor:
        raise HTTPException(status_code=404, detail="Guarantor not found")

    # Soft delete
    guarantor.is_deleted = True
    guarantor.deleted_at = datetime.utcnow()
    guarantor.deleted_by = current_user.user_id
    await db.commit()

    return {"message": f"Guarantor {guarantor_id} deleted successfully", "success": True}


@router.post("/{facility_id}/guarantors/{guarantor_id}/cheques")
async def add_cheque(
    facility_id: str,
    guarantor_id: str,
    cheque: ChequeCreate,
    current_user: TokenData = Depends(require_permission("write:facilities")),
    db: AsyncSession = Depends(get_db)
):
    """
    افزودن چک ضمانت
    """
    # Check guarantor exists
    guarantor_result = await db.execute(
        select(Guarantor).where(
            and_(
                Guarantor.id == guarantor_id,
                Guarantor.facility_id == facility_id,
                Guarantor.is_deleted == False
            )
        )
    )
    guarantor = guarantor_result.scalar_one_or_none()
    if not guarantor:
        raise HTTPException(status_code=404, detail="Guarantor not found")

    # Create cheque
    new_cheque = GuarantorCheque(
        guarantor_id=guarantor_id,
        cheque_no=cheque.cheque_no,
        bank_name=cheque.bank_name,
        amount=cheque.amount,
        cheque_date=cheque.cheque_date,
        status="Held",
        created_by=current_user.user_id
    )

    db.add(new_cheque)
    await db.commit()
    await db.refresh(new_cheque)

    return {
        "id": new_cheque.id,
        "guarantor_id": guarantor_id,
        "cheque_no": new_cheque.cheque_no,
        "bank_name": new_cheque.bank_name,
        "amount": float(new_cheque.amount) if new_cheque.amount else 0,
        "cheque_date": new_cheque.cheque_date.isoformat() if new_cheque.cheque_date else None,
        "status": new_cheque.status,
        "created_at": new_cheque.created_at.isoformat() if new_cheque.created_at else datetime.utcnow().isoformat()
    }


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
            {"code": "CreditCard", "name": "Credit Card", "name_fa": "کارت اعتباری"},
            {"code": "Other", "name": "Other", "name_fa": "سایر"},
        ]
    }
