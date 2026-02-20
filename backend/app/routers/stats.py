import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models import Facility, Customer

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics including total facilities amount, counts, etc.
    """
    try:
        # Run all queries - if any table is missing, the whole block fails
        # and we return zeros instead of cascading errors
        total_amount_result = await db.execute(select(func.coalesce(func.sum(Facility.amount), 0)))
        total_amount = total_amount_result.scalar() or 0

        facilities_count_result = await db.execute(select(func.count(Facility.id)))
        facilities_count = facilities_count_result.scalar() or 0

        customers_count_result = await db.execute(select(func.count(Customer.id)))
        customers_count = customers_count_result.scalar() or 0

        active_customers_result = await db.execute(
            select(func.count(Customer.id)).where(Customer.status == 'active')
        )
        active_customers = active_customers_result.scalar() or 0

        return {
            "total_facilities_amount": float(total_amount) if total_amount else 0.0,
            "facilities_count": facilities_count,
            "customers_count": customers_count,
            "active_customers": active_customers,
        }

    except SQLAlchemyError as e:
        logger.error(f"Dashboard stats database error: {e}")
        await db.rollback()
        # Return empty stats instead of 500 error for better UX
        return {
            "total_facilities_amount": 0.0,
            "facilities_count": 0,
            "customers_count": 0,
            "active_customers": 0,
        }
    except Exception as e:
        logger.error(f"Dashboard stats unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
