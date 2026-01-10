"""
Properties API Routes
روت‌های API برای مدیریت املاک و وثایق
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from decimal import Decimal

from app.core.security import get_current_user, TokenData
from app.core.database import get_db
from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus

router = APIRouter()


# ========== Schemas ==========
class PropertyBase(BaseModel):
    location: Optional[str] = "UAE"
    property_type: Optional[str] = "Apartment"
    status: Optional[str] = "Free"
    plate_no: Optional[str] = None
    deed_no: Optional[str] = None
    makani_no: Optional[str] = None
    ejari_no: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None
    building_name: Optional[str] = None
    unit_no: Optional[str] = None
    area_sqft: Optional[float] = None
    area_sqm: Optional[float] = None
    bedrooms: Optional[int] = None
    floors: Optional[int] = None
    purchase_value: Optional[float] = None
    purchase_date: Optional[date] = None
    current_value: Optional[float] = None
    valuation_date: Optional[date] = None
    mortgage_value: Optional[float] = None
    currency: Optional[str] = "AED"
    lien_amount: Optional[float] = None
    lien_date: Optional[date] = None
    lien_release_date: Optional[date] = None
    mortgage_bank: Optional[str] = None
    mortgage_reference: Optional[str] = None
    owner_name: Optional[str] = None
    ownership_percentage: Optional[float] = 100
    co_owners: Optional[List[dict]] = []
    notes: Optional[str] = None
    custom_fields: Optional[dict] = {}


class PropertyCreate(PropertyBase):
    customer_id: str


class PropertyUpdate(PropertyBase):
    pass


class PropertyResponse(PropertyBase):
    id: str
    customer_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    ltv_ratio: Optional[float] = 0

    class Config:
        from_attributes = True


# ========== Endpoints ==========
@router.get("")
async def list_properties(
    customer_id: Optional[str] = None,
    location: Optional[str] = None,
    property_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    لیست همه املاک با فیلتر و جستجو
    """
    query = select(Property).where(Property.is_deleted == False)

    # فیلترها
    if customer_id:
        query = query.where(Property.customer_id == customer_id)
    if location:
        query = query.where(Property.location == location)
    if property_type:
        query = query.where(Property.property_type == property_type)
    if status:
        query = query.where(Property.status == status)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Property.address.ilike(search_term),
                Property.building_name.ilike(search_term),
                Property.owner_name.ilike(search_term),
                Property.plate_no.ilike(search_term),
                Property.deed_no.ilike(search_term),
                Property.city.ilike(search_term)
            )
        )

    # تعداد کل
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # صفحه‌بندی
    query = query.order_by(Property.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    properties = result.scalars().all()

    return {
        "items": [
            {
                "id": p.id,
                "customer_id": p.customer_id,
                "location": p.location.value if p.location else None,
                "property_type": p.property_type.value if p.property_type else None,
                "status": p.status.value if p.status else None,
                "plate_no": p.plate_no,
                "deed_no": p.deed_no,
                "makani_no": p.makani_no,
                "address": p.address,
                "city": p.city,
                "area": p.area,
                "building_name": p.building_name,
                "unit_no": p.unit_no,
                "area_sqft": float(p.area_sqft) if p.area_sqft else None,
                "area_sqm": float(p.area_sqm) if p.area_sqm else None,
                "bedrooms": p.bedrooms,
                "current_value": float(p.current_value) if p.current_value else None,
                "purchase_value": float(p.purchase_value) if p.purchase_value else None,
                "mortgage_value": float(p.mortgage_value) if p.mortgage_value else None,
                "lien_amount": float(p.lien_amount) if p.lien_amount else None,
                "mortgage_bank": p.mortgage_bank,
                "owner_name": p.owner_name,
                "currency": p.currency,
                "notes": p.notes,
                "ltv_ratio": p.ltv_ratio,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in properties
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{property_id}")
async def get_property(
    property_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت جزئیات یک ملک
    """
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.is_deleted == False
        )
    )
    prop = result.scalar_one_or_none()

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return {
        "id": prop.id,
        "customer_id": prop.customer_id,
        "location": prop.location.value if prop.location else None,
        "property_type": prop.property_type.value if prop.property_type else None,
        "status": prop.status.value if prop.status else None,
        "plate_no": prop.plate_no,
        "deed_no": prop.deed_no,
        "makani_no": prop.makani_no,
        "ejari_no": prop.ejari_no,
        "address": prop.address,
        "city": prop.city,
        "area": prop.area,
        "building_name": prop.building_name,
        "unit_no": prop.unit_no,
        "area_sqft": float(prop.area_sqft) if prop.area_sqft else None,
        "area_sqm": float(prop.area_sqm) if prop.area_sqm else None,
        "bedrooms": prop.bedrooms,
        "floors": prop.floors,
        "purchase_value": float(prop.purchase_value) if prop.purchase_value else None,
        "purchase_date": prop.purchase_date.isoformat() if prop.purchase_date else None,
        "current_value": float(prop.current_value) if prop.current_value else None,
        "valuation_date": prop.valuation_date.isoformat() if prop.valuation_date else None,
        "mortgage_value": float(prop.mortgage_value) if prop.mortgage_value else None,
        "currency": prop.currency,
        "lien_amount": float(prop.lien_amount) if prop.lien_amount else None,
        "lien_date": prop.lien_date.isoformat() if prop.lien_date else None,
        "lien_release_date": prop.lien_release_date.isoformat() if prop.lien_release_date else None,
        "mortgage_bank": prop.mortgage_bank,
        "mortgage_reference": prop.mortgage_reference,
        "owner_name": prop.owner_name,
        "ownership_percentage": float(prop.ownership_percentage) if prop.ownership_percentage else 100,
        "co_owners": prop.co_owners or [],
        "notes": prop.notes,
        "custom_fields": prop.custom_fields or {},
        "ltv_ratio": prop.ltv_ratio,
        "created_at": prop.created_at.isoformat() if prop.created_at else None,
        "updated_at": prop.updated_at.isoformat() if prop.updated_at else None
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد ملک جدید
    """
    # تبدیل enum values
    location = None
    if property_data.location:
        try:
            location = PropertyLocation(property_data.location)
        except ValueError:
            location = PropertyLocation.UAE

    prop_type = None
    if property_data.property_type:
        try:
            prop_type = PropertyType(property_data.property_type)
        except ValueError:
            prop_type = PropertyType.APARTMENT

    prop_status = None
    if property_data.status:
        try:
            prop_status = PropertyStatus(property_data.status)
        except ValueError:
            prop_status = PropertyStatus.FREE

    new_property = Property(
        customer_id=property_data.customer_id,
        location=location,
        property_type=prop_type,
        status=prop_status,
        plate_no=property_data.plate_no,
        deed_no=property_data.deed_no,
        makani_no=property_data.makani_no,
        ejari_no=property_data.ejari_no,
        address=property_data.address,
        city=property_data.city,
        area=property_data.area,
        building_name=property_data.building_name,
        unit_no=property_data.unit_no,
        area_sqft=Decimal(str(property_data.area_sqft)) if property_data.area_sqft else None,
        area_sqm=Decimal(str(property_data.area_sqm)) if property_data.area_sqm else None,
        bedrooms=property_data.bedrooms,
        floors=property_data.floors,
        purchase_value=Decimal(str(property_data.purchase_value)) if property_data.purchase_value else None,
        purchase_date=property_data.purchase_date,
        current_value=Decimal(str(property_data.current_value)) if property_data.current_value else None,
        valuation_date=property_data.valuation_date,
        mortgage_value=Decimal(str(property_data.mortgage_value)) if property_data.mortgage_value else None,
        currency=property_data.currency,
        lien_amount=Decimal(str(property_data.lien_amount)) if property_data.lien_amount else None,
        lien_date=property_data.lien_date,
        lien_release_date=property_data.lien_release_date,
        mortgage_bank=property_data.mortgage_bank,
        mortgage_reference=property_data.mortgage_reference,
        owner_name=property_data.owner_name,
        ownership_percentage=Decimal(str(property_data.ownership_percentage)) if property_data.ownership_percentage else 100,
        co_owners=property_data.co_owners,
        notes=property_data.notes,
        custom_fields=property_data.custom_fields,
        created_by=current_user.user_id
    )

    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)

    return {
        "id": new_property.id,
        "message": "Property created successfully"
    }


@router.put("/{property_id}")
async def update_property(
    property_id: str,
    property_data: PropertyUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی ملک
    """
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.is_deleted == False
        )
    )
    prop = result.scalar_one_or_none()

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # بروزرسانی فیلدها
    update_data = property_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "location" and value:
            try:
                value = PropertyLocation(value)
            except ValueError:
                continue
        elif field == "property_type" and value:
            try:
                value = PropertyType(value)
            except ValueError:
                continue
        elif field == "status" and value:
            try:
                value = PropertyStatus(value)
            except ValueError:
                continue
        elif field in ["area_sqft", "area_sqm", "purchase_value", "current_value",
                       "mortgage_value", "lien_amount", "ownership_percentage"] and value is not None:
            value = Decimal(str(value))

        setattr(prop, field, value)

    prop.updated_by = current_user.user_id
    await db.commit()

    return {"message": "Property updated successfully"}


@router.delete("/{property_id}")
async def delete_property(
    property_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف ملک (soft delete)
    """
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.is_deleted == False
        )
    )
    prop = result.scalar_one_or_none()

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    prop.is_deleted = True
    prop.deleted_by = current_user.user_id
    await db.commit()

    return {"message": "Property deleted successfully"}


@router.get("/customer/{customer_id}")
async def get_customer_properties(
    customer_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    لیست املاک یک مشتری
    """
    result = await db.execute(
        select(Property).where(
            Property.customer_id == customer_id,
            Property.is_deleted == False
        ).order_by(Property.created_at.desc())
    )
    properties = result.scalars().all()

    return {
        "items": [
            {
                "id": p.id,
                "location": p.location.value if p.location else None,
                "property_type": p.property_type.value if p.property_type else None,
                "status": p.status.value if p.status else None,
                "address": p.address,
                "city": p.city,
                "building_name": p.building_name,
                "current_value": float(p.current_value) if p.current_value else None,
                "lien_amount": float(p.lien_amount) if p.lien_amount else None,
                "currency": p.currency,
                "ltv_ratio": p.ltv_ratio
            }
            for p in properties
        ],
        "total": len(properties)
    }


@router.get("/stats/summary")
async def get_properties_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    آمار کلی املاک
    """
    # تعداد کل
    total_result = await db.execute(
        select(func.count()).select_from(Property).where(Property.is_deleted == False)
    )
    total = total_result.scalar() or 0

    # تعداد به تفکیک وضعیت
    status_result = await db.execute(
        select(Property.status, func.count()).where(Property.is_deleted == False).group_by(Property.status)
    )
    by_status = {row[0].value if row[0] else "Unknown": row[1] for row in status_result.fetchall()}

    # تعداد به تفکیک موقعیت
    location_result = await db.execute(
        select(Property.location, func.count()).where(Property.is_deleted == False).group_by(Property.location)
    )
    by_location = {row[0].value if row[0] else "Unknown": row[1] for row in location_result.fetchall()}

    # مجموع ارزش
    value_result = await db.execute(
        select(func.sum(Property.current_value)).where(Property.is_deleted == False)
    )
    total_value = float(value_result.scalar() or 0)

    return {
        "total": total,
        "by_status": by_status,
        "by_location": by_location,
        "total_value": total_value
    }
