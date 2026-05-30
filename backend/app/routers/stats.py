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
from app.schemas.stats import (
    DashboardStatsResponse,
    TotalExposureResponse,
    RecentCustomerResponse,
    RecentActivityResponse,
)
from app.utils.security import get_current_user

# Authentication is required for every stats endpoint.
router = APIRouter(dependencies=[Depends(get_current_user)])
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Return aggregated dashboard statistics.

    The individual count queries degrade gracefully to ``0`` on error so a
    single missing optional column never blanks the whole dashboard. The
    monthly-revenue calculation is treated as critical: if it cannot be computed
    (e.g. the ``amount`` column is missing) the endpoint returns a clear
    ``500`` so the frontend can show an actionable error instead of a misleading
    zero.
    """
    try:
        # Total customers
        try:
            total_customers_result = await db.execute(
                select(func.count(Customer.id)).where(Customer.is_deleted == False)
            )
            total_customers = total_customers_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching total customers: %s", e)
            total_customers = 0

        # Active customers
        try:
            active_customers_result = await db.execute(
                select(func.count(Customer.id)).where(
                    and_(Customer.is_deleted == False, Customer.status == 'active')
                )
            )
            active_customers = active_customers_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching active customers: %s", e)
            active_customers = 0

        # Total facilities
        try:
            total_facilities_result = await db.execute(
                select(func.count(Facility.id)).where(Facility.is_deleted == False)
            )
            total_facilities = total_facilities_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching total facilities: %s", e)
            total_facilities = 0

        # Active facilities
        try:
            active_facilities_result = await db.execute(
                select(func.count(Facility.id)).where(
                    and_(Facility.is_deleted == False, Facility.status == 'active')
                )
            )
            active_facilities = active_facilities_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching active facilities: %s", e)
            active_facilities = 0

        # Facilities expiring soon (within 30 days). Both end_date and the newer
        # expiry_date columns are considered so the count is robust to whichever
        # column a record populated.
        try:
            today = datetime.utcnow().date()
            thirty_days_later = today + timedelta(days=30)
            expiring_soon_result = await db.execute(
                select(func.count(Facility.id)).where(
                    and_(
                        Facility.is_deleted == False,
                        func.coalesce(Facility.expiry_date, Facility.end_date) >= today,
                        func.coalesce(Facility.expiry_date, Facility.end_date)
                        <= thirty_days_later,
                    )
                )
            )
            expiring_soon = expiring_soon_result.scalar() or 0
        except Exception as e:
            logger.error("Error fetching expiring soon facilities: %s", e)
            expiring_soon = 0

        # Total exposure / outstanding
        try:
            total_exposure_result = await db.execute(
                select(func.coalesce(func.sum(Facility.amount), 0)).where(
                    Facility.is_deleted == False
                )
            )
            total_exposure_amount = float(total_exposure_result.scalar() or 0)
        except Exception as e:
            logger.error("Error fetching total exposure: %s", e)
            total_exposure_amount = 0.0

        try:
            total_outstanding_result = await db.execute(
                select(func.coalesce(func.sum(Facility.outstanding), 0)).where(
                    Facility.is_deleted == False
                )
            )
            total_outstanding = float(total_outstanding_result.scalar() or 0)
        except Exception as e:
            logger.error("Error fetching total outstanding: %s", e)
            total_outstanding = 0.0

        # Monthly revenue — CRITICAL. Computed as the monthly interest accrual of
        # active facilities (amount * interest_rate / 100 / 12). A failure here
        # (e.g. the amount column is missing) surfaces a clear 500 error.
        try:
            monthly_revenue_result = await db.execute(
                select(
                    func.coalesce(
                        func.sum(
                            Facility.amount
                            * func.coalesce(Facility.interest_rate, 0)
                            / 1200.0
                        ),
                        0,
                    )
                ).where(
                    and_(Facility.is_deleted == False, Facility.status == 'active')
                )
            )
            monthly_revenue = float(monthly_revenue_result.scalar() or 0)
        except Exception as e:
            logger.error("Error calculating monthly revenue: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Error calculating monthly revenue (amount column unavailable)",
            )

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
                .where(
                    and_(
                        Customer.is_deleted == False,
                        Customer.name.isnot(None),
                        Customer.name != "",
                    )
                )
                .order_by(Customer.created_at.desc())
                .limit(5)
            )
            recent_customers = recent_customers_result.scalars().all()
        except Exception as e:
            logger.error("Error fetching recent customers: %s", e)
            recent_customers = []

        recent_customers_response: List[RecentCustomerResponse] = []
        recent_activities_response: List[RecentActivityResponse] = []
        for index, customer in enumerate(recent_customers):
            try:
                recent_customers_response.append(
                    RecentCustomerResponse(
                        id=str(customer.id),
                        account_no=customer.account_no or "",
                        name=customer.name or "",
                        status=customer.status or "inactive",
                        created_at=customer.created_at,
                    )
                )
                recent_activities_response.append(
                    RecentActivityResponse(
                        id=index + 1,
                        action=f"New customer added: {customer.name or customer.account_no or customer.id}",
                        timestamp=customer.created_at,
                        user="system",
                    )
                )
            except Exception as e:
                logger.error(
                    "Error processing customer %s: %s",
                    getattr(customer, 'id', 'unknown'),
                    e,
                )
                continue

        return DashboardStatsResponse(
            total_customers=total_customers,
            active_customers=active_customers,
            total_facilities=total_facilities,
            active_facilities=active_facilities,
            expiring_soon=expiring_soon,
            expiring_facilities=expiring_soon,
            expiring_soon_facilities=expiring_soon,
            monthly_revenue=monthly_revenue,
            total_outstanding=total_outstanding,
            total_exposure=TotalExposureResponse(
                amount=total_exposure_amount, currency="AED"
            ),
            recent_customers=recent_customers_response,
            recent_activities=recent_activities_response,
        )
    except HTTPException:
        # Preserve explicit HTTP errors (e.g. the monthly-revenue 500) verbatim.
        raise
    except Exception as e:
        # Generic message only — never leak internals to the client (see the
        # log for the full error).
        logger.error("Critical error in dashboard stats endpoint: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching dashboard stats")
