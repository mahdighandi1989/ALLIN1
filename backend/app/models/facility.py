from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.models.user import User
from app.models.offer_letter import OfferLetter

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get dashboard statistics including total customers, facilities, offer letters, etc.
    """
    try:
        # Get total customers (excluding deleted)
        total_customers = db.query(Customer).filter(Customer.is_deleted == False).count()

        # Get total facilities (excluding deleted)
        total_facilities = db.query(Facility).filter(Facility.is_deleted == False).count()

        # Get total offer letters (excluding deleted)
        total_offer_letters = db.query(OfferLetter).filter(OfferLetter.is_deleted == False).count()

        # Get active facilities count
        active_facilities = db.query(Facility).filter(
            Facility.is_deleted == False,
            Facility.status == 'active'
        ).count()

        # Get recent customers (last 30 days)
        # from datetime import datetime, timedelta
        # thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        # recent_customers = db.query(Customer).filter(Customer.created_at >= thirty_days_ago).count()

        # For now, we'll just use 0 for recent customers
        recent_customers = 0

        # Calculate total exposure (sum of outstanding amounts for active facilities)
        # We need to import func for sum
        from sqlalchemy import func
        exposure_result = db.query(func.sum(Facility.outstanding)).filter(
            Facility.is_deleted == False,
            Facility.status == 'active'
        ).scalar()
        total_exposure = exposure_result if exposure_result else 0

        return {
            "total_customers": total_customers,
            "total_facilities": total_facilities,
            "total_offer_letters": total_offer_letters,
            "active_facilities": active_facilities,
            "recent_customers": recent_customers,
            "total_exposure": float(total_exposure) if total_exposure else 0.0
        }
    except Exception as e:
        # Log the exception for debugging
        # You can use a logger here
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")