from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from app.database import get_db
from app.models import Facility, Customer

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics including total facilities amount, counts, etc.
    """
    try:
        # Total facilities amount with proper error handling
        try:
            total_amount_result = await db.execute(select(func.sum(Facility.amount)))
            total_amount = total_amount_result.scalar() or 0
        except ProgrammingError:
            # If amount column doesn't exist or has issues, default to 0
            total_amount = 0
        
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
        
    except SQLAlchemyError as e:
        # Rollback any failed transaction
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error occurred: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )