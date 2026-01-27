```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.facility import Facility
from ..schemas.facility import (
    FacilityCreate, 
    FacilityUpdate, 
    FacilityResponse,
    FacilityListResponse
)
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.post("/", response_model=FacilityResponse)
async def create_facility(
    facility_data: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ایجاد تسهیلات جدید"""
    try:
        # بررسی وجود تسهیلات با همان شماره قرارداد
        existing_facility = await db.execute(
            select(Facility).where(Facility.contract_number == facility_data.contract_number)
        )
        if existing_facility.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="تسهیلاتی با این شماره قرارداد قبلاً ثبت شده است"
            )

        # ایجاد تسهیلات جدید
        facility = Facility(
            **facility_data.model_dump(),
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(facility)
        await db.commit()
        await db.refresh(facility)
        
        return facility
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در ایجاد تسهیلات: {str(e)}"
        )

@router.get("/", response_model=FacilityListResponse)
async def get_facilities(
    skip: int = 0,
    limit: int = 100,
    customer_name: Optional[str] = None,
    facility_type: Optional[str] = None,
    status: Optional[str] = None,
    branch_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت لیست تسهیلات با فیلتر"""
    try:
        query = select(Facility)
        
        # اعمال فیلترها
        conditions = []
        
        if customer_name:
            conditions.append(Facility.customer_name.ilike(f"%{customer_name}%"))
        
        if facility_type:
            conditions.append(Facility.facility_type == facility_type)
            
        if status:
            conditions.append(Facility.status == status)
            
        if branch_code:
            conditions.append(Facility.branch_code == branch_code)
        
        # اگر کاربر admin نیست، فقط تسهیلات خودش را ببیند
        if current_user.role != "admin":
            conditions.append(Facility.created_by == current_user.id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # اعمال pagination
        query = query.offset(skip).limit(limit).order_by(Facility.created_at.desc())
        
        result = await db.execute(query)
        facilities = result.scalars().all()
        
        # شمارش کل رکوردها
        count_query = select(Facility)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return FacilityListResponse(
            facilities=facilities,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت لیست تسهیلات: {str(e)}"
        )

@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """دریافت اطلاعات یک تسهیلات"""
    try:
        query = select(Facility).where(Facility.id == facility_id)
        
        # اگر کاربر admin نیست، فقط تسهیلات خودش را ببیند
        if current_user.role != "admin":
            query = query.where(Facility.created_by == current_user.id)
        
        result = await db.execute(query)
        facility = result.scalar_one_or_none()
        
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="تسهیلات مورد نظر یافت نشد"
            )
        
        return facility
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت اطلاعات تسهیلات: {str(e)}"
        )

@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: int,
    facility_data: FacilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ویرایش تسهیلات"""
    try:
        query = select(Facility).where(Facility.id == facility_id)
        
        # اگر کاربر admin نیست، فقط تسهیلات خودش را ویرایش کند
        if current_user.role != "admin":
            query = query.where(Facility.created_by == current_user.id)
        
        result = await db.execute(query)
        facility = result.scalar_one_or_none()
        
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="تسهیلات مورد نظر یافت نشد"
            )
        
        # بررسی تغییر شماره قرارداد
        if (facility_data.contract_number and 
            facility_data.contract_number != facility.contract_number):
            existing_facility = await db.execute(
                select(Facility).where(
                    and_(
                        Facility.contract_number == facility_data.contract_number,
                        Facility.id != facility_id
                    )
                )
            )
            if existing_facility.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="تسهیلاتی با این شماره قرارداد قبلاً ثبت شده است"
                )
        
        # ویرایش فیلدها
        update_data = facility_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(facility, field, value)
        
        facility.updated_at = datetime.utcnow()
        facility.updated_by = current_user.id
        
        await db.commit()
        await db.refresh(facility)
        
        return facility
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در ویرایش تسهیلات: {str(e)}"
        )

@router.delete("/{facility_id}")
async def delete_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """حذف تسهیلات"""
    try:
        # فقط admin می‌تواند تسهیلات را حذف کند
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="شما مجوز حذف تسهیلات را ندارید"
            )
        
        result = await db.execute(
            select(Facility).where(Facility.id == facility_id)
        )
        facility = result.scalar_one_or_none()
        
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="تسهیلات مورد نظر یافت نشد"
            )
        
        await db.delete(facility)
        await db.commit()
        
        return {"message": "تسهیلات با موفقیت حذف شد"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در حذف تسهیلات: {str(e)}"
        )

@router.get("/search/advanced")
async def advanced_search_facilities(
    contract_number: Optional[str] = None,
    customer_national_id: Optional[str] = None,
    amount_from: Optional[float] = None,
    amount_to: Optional[float] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """جستجوی پیشرفته تسهیلات"""
    try:
        query = select(Facility)
        conditions = []
        
        if contract_number:
            conditions.append(Facility.contract_number.ilike(f"%{contract_number}%"))
        
        if customer_national_id:
            conditions.append(Facility.customer_national_id == customer_national_id)
        
        if amount_from is not None:
            conditions.append(Facility.amount >= amount_from)
        
        if amount_to is not None:
            conditions.append(Facility.amount <= amount_to)
        
        if date_from:
            conditions.append(Facility.contract_date >= date_from)
        
        if date_to:
            conditions.append(Facility.contract_date <= date_to)
        
        # اگر کاربر admin نیست، فقط تسهیلات خودش را ببیند
        if current_user.role != "admin":
            conditions.append(Facility.created_by == current_user.id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(Facility.created_at.desc())
        
        result = await db.execute(query)
        facilities = result.scalars().all()
        
        return {
            "facilities": facilities,
            "total": len(facilities),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در جستجوی پیشرفته: {str(e)}"
        )

@router.get("/statistics/summary")
async def get_facilities_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """آمار کلی تسهیلات"""
    try:
        query = select(Facility)
        
        # اگر کاربر admin نیست، فقط تسهیلات خودش را ببیند
        if current_user.role != "admin":
            query = query.where(Facility.created_by == current_user.id)
        
        result = await db.execute(query)
        facilities = result.scalars().all()
        
        total_count = len(facilities)
        total_amount = sum(f.amount for f in facilities if f.amount)
        
        # آمار بر اساس وضعیت
        status_stats = {}
        for facility in facilities:
            status = facility.status or "نامشخص"
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # آمار بر اساس نوع تسهیلات
        type_stats = {}
        for facility in facilities:
            facility_type = facility.facility_type or "نامشخص"
            type_stats[facility_type] = type_stats.get(facility_type, 0) + 1
        
        return {
            "total_count": total_count,
            "total_amount": total_amount,
            "status_statistics": status_stats,
            "type_statistics": type_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت آمار: {str(e)}"
        )

@router.patch("/{facility_id}/status")
async def update_facility_status(
    facility_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تغییر وضعیت تسهیلات"""
    try:
        query = select(Facility).where(Facility.id == facility_id)
        
        # اگر کاربر admin نیست، فقط تسهیلات خودش را ویرایش کند
        if current_user.role != "admin":
            query = query.where(Facility.created_by == current_user.id)
        
        result = await db.execute(query)
        facility = result.scalar_one_or_none()
        
        if not facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="تسهیلات مورد نظر یافت نشد"
            )
        
        # لیست وضعیت‌های مجاز
        valid_statuses = ["فعال", "غیرفعال", "تسویه", "معوق", "مشکوک", "معدوم"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"وضعیت نامعتبر. وضعیت‌های مجاز: {', '.join(valid_statuses)}"
            )
        
        facility.status = new_status
        facility.updated_at = datetime.utcnow()
        facility.updated_by = current_user.id