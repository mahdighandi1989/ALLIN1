from sqlalchemy import select, func, and_
from sqlalchemy.orm import load_only
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.schemas.stats import DashboardStatsResponse, TotalExposureResponse, RecentCustomerResponse
from app.utils.security import get_current_user

# Authentication is required for every stats endpoint.
router = APIRouter(dependencies=[Depends(get_current_user)])
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics
    """
    try:
        # Total customers
        try:
            total_customers_result = await db.execute(
                select(func.count(Customer.id)).where(Customer.is_deleted == False)
            )
            total_customers = total_customers_result.scalar() or 0
        except Exception as e:
            logger.error(f"Error fetching total customers: {str(e)}")
            total_customers = 0

        # Active customers
        try:
            active_customers_result = await db.execute(
                select(func.count(Customer.id)).where(
                    and_(
                        Customer.is_deleted == False,
                        Customer.status == 'active'
                    )
                )
            )
            active_customers = active_customers_result.scalar() or 0
        except Exception as e:
            logger.error(f"Error fetching active customers: {str(e)}")
            active_customers = 0

        # Total facilities
        try:
            total_facilities_result = await db.execute(
                select(func.count(Facility.id)).where(Facility.is_deleted == False)
            )
            total_facilities = total_facilities_result.scalar() or 0
        except Exception as e:
            logger.error(f"Error fetching total facilities: {str(e)}")
            total_facilities = 0

        # Facilities expiring soon (within 30 days)
        try:
            today = datetime.utcnow().date()
            thirty_days_later = today + timedelta(days=30)

            expiring_soon_result = await db.execute(
                select(func.count(Facility.id)).where(
                    and_(
                        Facility.is_deleted == False,
                        Facility.end_date >= today,
                        Facility.end_date <= thirty_days_later
                    )
                )
            )
            expiring_soon_facilities = expiring_soon_result.scalar() or 0
        except Exception as e:
            logger.error(f"Error fetching expiring soon facilities: {str(e)}")
            expiring_soon_facilities = 0

        # Total exposure
        try:
            total_exposure_result = await db.execute(
                select(func.coalesce(func.sum(Facility.amount), 0)).where(Facility.is_deleted == False)
            )
            total_exposure_amount = total_exposure_result.scalar() or 0
            if total_exposure_amount is None:
                total_exposure_amount = 0
        except Exception as e:
            logger.error(f"Error fetching total exposure: {str(e)}")
            total_exposure_amount = 0

        # Recent customers (last 5)
        try:
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
                    Customer.name.isnot(None),
                    Customer.name != ""
                ))
                .order_by(Customer.created_at.desc())
                .limit(5)
            )
            recent_customers = recent_customers_result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching recent customers: {str(e)}")
            recent_customers = []

        # Prepare recent customers response with null checks
        recent_customers_response = []
        for customer in recent_customers:
            try:
                recent_customers_response.append(
                    RecentCustomerResponse(
                        id=customer.id,
                        account_no=customer.account_no or "",
                        name=customer.name or "",
                        status=customer.status or "inactive",
                        created_at=customer.created_at
                    )
                )
            except Exception as e:
                logger.error(f"Error processing customer {getattr(customer, 'id', 'unknown')}: {str(e)}")
                continue

        return DashboardStatsResponse(
            total_customers=total_customers,
            active_customers=active_customers,
            total_facilities=total_facilities,
            expiring_soon_facilities=expiring_soon_facilities,
            total_exposure=TotalExposureResponse(
                amount=float(total_exposure_amount),
                currency="AED"
            ),
            recent_customers=recent_customers_response
        )
    except Exception as e:
        logger.error(f"Critical error in dashboard stats endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")