from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.utils.security import get_current_user

router = APIRouter()

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get dashboard statistics.
    """
    try:
        # Total customers count
        total_customers_result = await db.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
        total_customers = total_customers_result.scalar() or 0

        # Total facilities amount
        total_amount_result = await db.execute(
            select(func.sum(Facility.amount)).where(Facility.is_deleted == False)
        )
        total_amount = total_amount_result.scalar() or 0

        # Total outstanding
        total_outstanding_result = await db.execute(
            select(func.sum(Facility.outstanding)).where(Facility.is_deleted == False)
        )
        total_outstanding = total_outstanding_result.scalar() or 0

        # Facilities by type
        facilities_by_type_result = await db.execute(
            select(Facility.facility_type, func.count(Facility.id))
            .where(Facility.is_deleted == False)
            .group_by(Facility.facility_type)
        )
        facilities_by_type = dict(facilities_by_type_result.all())

        # Recent facilities (last 5)
        recent_facilities_result = await db.execute(
            select(Facility)
            .where(Facility.is_deleted == False)
            .order_by(Facility.created_at.desc())
            .limit(5)
        )
        recent_facilities = recent_facilities_result.scalars().all()

        # Customers by account type
        customers_by_type_result = await db.execute(
            select(Customer.account_type, func.count(Customer.id))
            .where(Customer.is_deleted == False)
            .group_by(Customer.account_type)
        )
        customers_by_type = dict(customers_by_type_result.all())

        return {
            "total_customers": total_customers,
            "total_amount": total_amount,
            "total_outstanding": total_outstanding,
            "facilities_by_type": facilities_by_type,
            "customers_by_type": customers_by_type,
            "recent_facilities": [
                {
                    "id": fac.id,
                    "name": fac.name,
                    "amount": fac.amount,
                    "customer_name": fac.customer_name,
                    "created_at": fac.created_at
                }
                for fac in recent_facilities
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@router.get("/customers/summary", response_model=Dict[str, Any])
async def get_customers_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get customers summary statistics.
    """
    try:
        # Total customers by status
        customers_by_status_result = await db.execute(
            select(Customer.status, func.count(Customer.id))
            .where(Customer.is_deleted == False)
            .group_by(Customer.status)
        )
        customers_by_status = dict(customers_by_status_result.all())

        # New customers this month
        # This would require a date filter; for simplicity, we return total
        return {
            "customers_by_status": customers_by_status,
            "total_customers": sum(customers_by_status.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customer summary: {str(e)}")

@router.get("/facilities/summary", response_model=Dict[str, Any])
async def get_facilities_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get facilities summary statistics.
    """
    try:
        # Facilities by status
        facilities_by_status_result = await db.execute(
            select(Facility.status, func.count(Facility.id))
            .where(Facility.is_deleted == False)
            .group_by(Facility.status)
        )
        facilities_by_status = dict(facilities_by_status_result.all())

        # Total amount by currency
        amount_by_currency_result = await db.execute(
            select(Facility.currency, func.sum(Facility.amount))
            .where(Facility.is_deleted == False)
            .group_by(Facility.currency)
        )
        amount_by_currency = dict(amount_by_currency_result.all())

        return {
            "facilities_by_status": facilities_by_status,
            "amount_by_currency": amount_by_currency
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching facilities summary: {str(e)}")