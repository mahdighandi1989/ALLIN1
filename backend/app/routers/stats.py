import logging
import decimal
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models import Facility, Customer, FacilityStatus, CustomerStatus
from app.schemas.stats import DashboardStatsResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics with structured, validated response.
    Uses response_model to ensure proper serialization of all data.
    """
    try:
        # Total Customers
        total_customers_result = await db.execute(
            select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
        )
        total_customers = total_customers_result.scalar() or 0

        # Active Customers
        active_customers_result = await db.execute(
            select(func.count()).select_from(Customer).where(
                and_(Customer.is_deleted == False, Customer.status == CustomerStatus.ACTIVE)
            )
        )
        active_customers = active_customers_result.scalar() or 0

        # Total Facilities
        total_facilities_result = await db.execute(
            select(func.count()).select_from(Facility).where(Facility.is_deleted == False)
        )
        total_facilities = total_facilities_result.scalar() or 0

        # Expiring Soon Facilities (within 30 days)
        thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
        expiring_soon_result = await db.execute(
            select(func.count()).select_from(Facility).where(
                and_(
                    Facility.is_deleted == False,
                    Facility.status == FacilityStatus.ACTIVE,
                    Facility.expiry_date <= thirty_days_from_now,
                    Facility.expiry_date >= datetime.utcnow()
                )
            )
        )
        expiring_soon = expiring_soon_result.scalar() or 0

        # Total Exposure (sum of active facility amounts)
        total_exposure_result = await db.execute(
            select(func.coalesce(func.sum(Facility.amount), 0)).where(
                and_(
                    Facility.is_deleted == False,
                    Facility.status == FacilityStatus.ACTIVE
                )
            )
        )
        total_exposure_amount = total_exposure_result.scalar() or decimal.Decimal('0.0')

        # Recent Customers (last 5)
        recent_customers_result = await db.execute(
            select(Customer)
            .where(Customer.is_deleted == False)
            .order_by(Customer.created_at.desc())
            .limit(5)
        )
        recent_customers = recent_customers_result.scalars().all()

        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_facilities": total_facilities,
            "expiring_soon_facilities": expiring_soon,
            "total_exposure": {
                "amount": float(total_exposure_amount),
                "currency": "AED",
            },
            "recent_customers": recent_customers,
        }

    except SQLAlchemyError as e:
        logger.error(f"Dashboard stats database error: {e}")
        await db.rollback()
        return {
            "total_customers": 0,
            "active_customers": 0,
            "total_facilities": 0,
            "expiring_soon_facilities": 0,
            "total_exposure": {"amount": 0.0, "currency": "AED"},
            "recent_customers": [],
        }
