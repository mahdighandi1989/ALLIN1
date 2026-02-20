from sqlalchemy import select, func, and_
from sqlalchemy.orm import load_only
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.schemas.stats import DashboardStatsResponse, TotalExposureResponse, RecentCustomerResponse

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics
    """
    try:
        # Total customers
        total_customers_result = await db.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
        total_customers = total_customers_result.scalar() or 0

        # Active customers
        active_customers_result = await db.execute(
            select(func.count(Customer.id)).where(
                and_(
                    Customer.is_deleted == False,
                    Customer.status == 'active'
                )
            )
        )
        active_customers = active_customers_result.scalar() or 0

        # Total facilities
        total_facilities_result = await db.execute(
            select(func.count(Facility.id)).where(Facility.is_deleted == False)
        )
        total_facilities = total_facilities_result.scalar() or 0

        # Facilities expiring soon (within 30 days)
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        thirty_days_later = today + timedelta(days=30)

        expiring_soon_result = await db.execute(
            select(func.count(Facility.id)).where(
                and_(
                    Facility.is_deleted == False,
                    Facility.expiry_date >= today,
                    Facility.expiry_date <= thirty_days_later
                )
            )
        )
        expiring_soon_facilities = expiring_soon_result.scalar() or 0

        # Total exposure
        total_exposure_result = await db.execute(
            select(func.coalesce(func.sum(Facility.amount), 0)).where(Facility.is_deleted == False)
        )
        total_exposure_amount = total_exposure_result.scalar() or 0

        # Recent customers (last 5)
        recent_customers_result = await db.execute(
            select(Customer)
            .options(
                load_only(
                    Customer.id,
                    Customer.account_no,
                    Customer.name,
                    Customer.status,
                    Customer.created_at,
                )
            )
            .where(and_(
                Customer.is_deleted == False,
                Customer.name.isnot(None),  # فیلتر کردن نام‌های null
                Customer.name != ""  # فیلتر کردن نام‌های خالی
            ))
            .order_by(Customer.created_at.desc())
            .limit(5)
        )
        recent_customers = recent_customers_result.scalars().all()

        return DashboardStatsResponse(
            total_customers=total_customers,
            active_customers=active_customers,
            total_facilities=total_facilities,
            expiring_soon_facilities=expiring_soon_facilities,
            total_exposure=TotalExposureResponse(
                amount=float(total_exposure_amount),
                currency="AED"
            ),
            recent_customers=[
                RecentCustomerResponse(
                    id=customer.id,
                    account_no=customer.account_no,
                    name=customer.name,
                    status=customer.status,
                    created_at=customer.created_at
                )
                for customer in recent_customers
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")