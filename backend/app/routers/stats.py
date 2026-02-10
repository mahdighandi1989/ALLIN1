from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Facility, Customer

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics including total facilities amount, counts, etc.
    """
    # Total facilities amount
    total_amount_result = await db.execute(select(func.sum(Facility.amount)))
    total_amount = total_amount_result.scalar() or 0
    
    # Facilities count
    facilities_count_result = await db.execute(select(func.count(Facility.id)))
    facilities_count = facilities_count_result.scalar() or 0
    
    # Customers count
    customers_count_result = await db.execute(select(func.count(Customer.id)))
    customers_count = customers_count_result.scalar() or 0
    
    # Active customers count (status = 'active')
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
