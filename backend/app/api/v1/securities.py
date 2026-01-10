"""
Securities API
API اوراق بهادار و ضمانت‌ها
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.security import Security, SecurityCategory, SecurityStatus

router = APIRouter()


# Schemas
class SecurityResponse(BaseModel):
    id: str
    customer_id: Optional[str]
    account_no: Optional[str]
    security_no: Optional[int]
    branch: Optional[str]
    customer_name: Optional[str]
    category: str
    year: Optional[int]
    month: Optional[str]
    has_fd: bool
    fd_details: Optional[str]
    guarantors: List[str]
    cheque_numbers: List[str]
    issuing_bank: Optional[str]
    cheque_amount_aed: Optional[float]
    undertaking_127: Optional[str]
    guarantee_128: Optional[str]
    credit_facility_agreement: Optional[str]
    original_offer_letter: Optional[str]
    property_no: Optional[str]
    mortgage_amount_aed: Optional[float]
    property_location: Optional[str]
    safe_box: Optional[str]
    stored_date: Optional[date]
    taken_out_date: Optional[date]
    status: str
    remarks: Optional[str]

    class Config:
        from_attributes = True


@router.get("")
async def get_securities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """دریافت لیست اوراق بهادار"""
    query = select(Security).where(Security.is_deleted == False)

    if category:
        try:
            cat_enum = SecurityCategory(category)
            query = query.where(Security.category == cat_enum)
        except:
            pass
    if year:
        query = query.where(Security.year == year)
    if status:
        try:
            status_enum = SecurityStatus(status)
            query = query.where(Security.status == status_enum)
        except:
            pass
    if customer_id:
        query = query.where(Security.customer_id == customer_id)
    if search:
        query = query.where(
            or_(
                Security.customer_name.ilike(f"%{search}%"),
                Security.account_no.ilike(f"%{search}%"),
                Security.branch.ilike(f"%{search}%")
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(Security.year.desc(), Security.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    securities = result.scalars().all()

    return {
        "items": [
            {
                "id": s.id,
                "customer_id": s.customer_id,
                "account_no": s.account_no,
                "security_no": s.security_no,
                "branch": s.branch,
                "customer_name": s.customer_name,
                "category": s.category.value if s.category else "Retail",
                "year": s.year,
                "month": s.month,
                "has_fd": s.has_fd,
                "fd_details": s.fd_details,
                "guarantors": s.guarantors or [],
                "cheque_numbers": s.cheque_numbers or [],
                "issuing_bank": s.issuing_bank,
                "cheque_amount_aed": float(s.cheque_amount_aed) if s.cheque_amount_aed else None,
                "undertaking_127": s.undertaking_127,
                "guarantee_128": s.guarantee_128,
                "credit_facility_agreement": s.credit_facility_agreement,
                "original_offer_letter": s.original_offer_letter,
                "property_no": s.property_no,
                "mortgage_amount_aed": float(s.mortgage_amount_aed) if s.mortgage_amount_aed else None,
                "property_location": s.property_location,
                "safe_box": s.safe_box,
                "stored_date": s.stored_date.isoformat() if s.stored_date else None,
                "taken_out_date": s.taken_out_date.isoformat() if s.taken_out_date else None,
                "status": s.status.value if s.status else "Active",
                "remarks": s.remarks,
            }
            for s in securities
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats")
async def get_security_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """دریافت آمار اوراق بهادار"""
    # Total
    total_result = await db.execute(
        select(func.count()).select_from(Security).where(Security.is_deleted == False)
    )
    total = total_result.scalar() or 0

    # By category
    category_counts = {}
    for cat in SecurityCategory:
        result = await db.execute(
            select(func.count()).select_from(Security).where(
                Security.is_deleted == False,
                Security.category == cat
            )
        )
        category_counts[cat.value] = result.scalar() or 0

    # By year
    year_counts = {}
    year_query = select(Security.year, func.count()).where(
        Security.is_deleted == False,
        Security.year.isnot(None)
    ).group_by(Security.year).order_by(Security.year.desc())
    year_result = await db.execute(year_query)
    for year, count in year_result.all():
        if year:
            year_counts[str(year)] = count

    return {
        "total": total,
        "by_category": category_counts,
        "by_year": year_counts
    }


@router.get("/years")
async def get_available_years(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """دریافت سال‌های موجود"""
    query = select(Security.year).distinct().where(
        Security.is_deleted == False,
        Security.year.isnot(None)
    ).order_by(Security.year.desc())
    result = await db.execute(query)
    years = [y for (y,) in result.all() if y]
    return {"years": years}


@router.get("/{security_id}")
async def get_security(
    security_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """دریافت یک رکورد اوراق بهادار"""
    result = await db.execute(
        select(Security).where(
            Security.id == security_id,
            Security.is_deleted == False
        )
    )
    security = result.scalar_one_or_none()

    if not security:
        raise HTTPException(status_code=404, detail="Security record not found")

    return {
        "id": security.id,
        "customer_id": security.customer_id,
        "account_no": security.account_no,
        "security_no": security.security_no,
        "branch": security.branch,
        "customer_name": security.customer_name,
        "category": security.category.value if security.category else "Retail",
        "year": security.year,
        "month": security.month,
        "has_fd": security.has_fd,
        "fd_details": security.fd_details,
        "guarantors": security.guarantors or [],
        "cheque_numbers": security.cheque_numbers or [],
        "issuing_bank": security.issuing_bank,
        "cheque_amount_aed": float(security.cheque_amount_aed) if security.cheque_amount_aed else None,
        "undertaking_127": security.undertaking_127,
        "guarantee_128": security.guarantee_128,
        "credit_facility_agreement": security.credit_facility_agreement,
        "original_offer_letter": security.original_offer_letter,
        "property_no": security.property_no,
        "mortgage_amount_aed": float(security.mortgage_amount_aed) if security.mortgage_amount_aed else None,
        "property_location": security.property_location,
        "safe_box": security.safe_box,
        "stored_date": security.stored_date.isoformat() if security.stored_date else None,
        "taken_out_date": security.taken_out_date.isoformat() if security.taken_out_date else None,
        "status": security.status.value if security.status else "Active",
        "remarks": security.remarks,
        "source_file": security.source_file,
    }
