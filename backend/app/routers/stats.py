from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import func, select
from app.models.customer import Customer
from app.models.facility import Facility

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    try:
        # Total customers
        total_customers_result = await db.execute(select(func.count(Customer.id)))
        total_customers = total_customers_result.scalar() or 0

        # Active customers
        active_customers_result = await db.execute(
            select(func.count(Customer.id)).where(Customer.status == "active")
        )
        active_customers = active_customers_result.scalar() or 0

        # Total facilities
        total_facilities_result = await db.execute(select(func.count(Facility.id)))
        total_facilities = total_facilities_result.scalar() or 0

        # Total facility amount
        total_amount_result = await db.execute(select(func.sum(Facility.amount)))
        total_amount = total_amount_result.scalar() or 0

        # Active facilities
        active_facilities_result = await db.execute(
            select(func.count(Facility.id)).where(Facility.status == "active")
        )
        active_facilities = active_facilities_result.scalar() or 0

        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_facilities": total_facilities,
            "total_amount": float(total_amount) if total_amount else 0,
            "active_facilities": active_facilities,
            "inactive_customers": total_customers - active_customers,
            "inactive_facilities": total_facilities - active_facilities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")