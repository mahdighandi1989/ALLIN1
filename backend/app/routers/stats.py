from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.models.customer import Customer, CustomerStatus
from app.models.facility import Facility, FacilityStatus
from app.schemas.stats import DashboardStats

router = APIRouter()

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard statistics for the current user.
    """
    try:
        # Get customer statistics
        customers_query = select(
            func.count(Customer.id).label("total"),
            func.sum(
                func.case((Customer.status == CustomerStatus.ACTIVE, 1), else_=0)
            ).label("active")
        ).where(Customer.is_deleted == False)
        
        customers_result = await db.execute(customers_query)
        customers_data = customers_result.first()
        
        # Get facility statistics
        facilities_query = select(
            func.count(Facility.id).label("total"),
            func.sum(Facility.amount).label("total_amount"),
            func.sum(Facility.outstanding).label("outstanding")
        ).where(Facility.status == FacilityStatus.ACTIVE)
        
        facilities_result = await db.execute(facilities_query)
        facilities_data = facilities_result.first()
        
        # Calculate expiring soon (within 30 days)
        expiring_date = datetime.now() + timedelta(days=30)
        expiring_query = select(func.count(Facility.id)).where(
            Facility.expiry_date <= expiring_date,
            Facility.expiry_date >= datetime.now(),
            Facility.status == FacilityStatus.ACTIVE
        )
        expiring_result = await db.execute(expiring_query)
        expiring_soon = expiring_result.scalar() or 0
        
        # Get recent customers (last 5)
        recent_customers_query = select(Customer).where(
            Customer.is_deleted == False
        ).order_by(Customer.created_at.desc()).limit(5)
        
        recent_customers_result = await db.execute(recent_customers_query)
        recent_customers = recent_customers_result.scalars().all()
        
        # Get recent facilities (last 5)
        recent_facilities_query = select(Facility).where(
            Facility.status == FacilityStatus.ACTIVE
        ).order_by(Facility.created_at.desc()).limit(5)
        
        recent_facilities_result = await db.execute(recent_facilities_query)
        recent_facilities = recent_facilities_result.scalars().all()
        
        # Format recent customers
        formatted_recent_customers = [
            {
                "id": str(customer.id),
                "name": customer.name,
                "email": customer.email or "",
                "phone": customer.phone or "",
                "status": customer.status
            }
            for customer in recent_customers
        ]
        
        # Format recent facilities
        formatted_recent_facilities = []
        for facility in recent_facilities:
            # Get customer name
            customer_query = select(Customer.name).where(Customer.id == facility.customer_id)
            customer_result = await db.execute(customer_query)
            customer_name = customer_result.scalar() or "Unknown"
            
            formatted_recent_facilities.append({
                "id": str(facility.id),
                "customer_id": str(facility.customer_id),
                "customer_name": customer_name,
                "type": facility.facility_type,
                "amount": float(facility.amount) if facility.amount else 0.0,
                "status": facility.status,
                "issue_date": facility.start_date.isoformat() if facility.start_date else "",
                "expiry_date": facility.expiry_date.isoformat() if facility.expiry_date else ""
            })
        
        return {
            "customers": {
                "total": customers_data.total or 0,
                "active": customers_data.active or 0
            },
            "facilities": {
                "total": facilities_data.total or 0,
                "expiring_soon": expiring_soon,
                "total_amount": float(facilities_data.total_amount) if facilities_data.total_amount else 0.0,
                "outstanding": float(facilities_data.outstanding) if facilities_data.outstanding else 0.0
            },
            "recent_customers": formatted_recent_customers,
            "recent_facilities": formatted_recent_facilities
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving dashboard statistics: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for stats module."""
    return {"status": "healthy", "module": "stats"}