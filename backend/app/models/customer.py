"""Stats Router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.models.user import User
from app.models.booking import Booking

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get dashboard statistics"""
    try:
        # Customer stats
        total_customers = db.query(Customer).filter(Customer.is_deleted == False).count()
        active_customers = db.query(Customer).filter(
            Customer.is_deleted == False,
            Customer.status == "active"
        ).count()

        # Facility stats
        total_facilities = db.query(Facility).filter(Facility.is_deleted == False).count()
        available_facilities = db.query(Facility).filter(
            Facility.is_deleted == False,
            Facility.status == "available"
        ).count()

        # User stats
        total_users = db.query(User).filter(User.is_deleted == False).count()

        # Booking stats
        total_bookings = db.query(Booking).filter(Booking.is_deleted == False).count()
        pending_bookings = db.query(Booking).filter(
            Booking.is_deleted == False,
            Booking.status == "pending"
        ).count()

        return {
            "customers": {
                "total": total_customers,
                "active": active_customers
            },
            "facilities": {
                "total": total_facilities,
                "available": available_facilities
            },
            "users": {
                "total": total_users
            },
            "bookings": {
                "total": total_bookings,
                "pending": pending_bookings
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))