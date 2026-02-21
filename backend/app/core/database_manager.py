from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from backend.app.core.database import get_db
from backend.app.models import Customer, Facility, User, Transaction
from backend.app.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics including counts, recent activity, etc.
    """
    try:
        db_manager = DatabaseManager(db)
        
        # Get table counts with error handling for each query
        stats = {}
        
        # Count customers - handle case where table might not exist or query fails
        try:
            customers_count = await db.execute(
                "SELECT COUNT(*) FROM customers WHERE deleted_at IS NULL"
            )
            stats["total_customers"] = customers_count.scalar() or 0
        except Exception as e:
            logger.warning(f"Failed to count customers: {e}")
            stats["total_customers"] = 0
        
        # Count facilities - handle different possible table names or schemas
        try:
            facilities_count = await db.execute(
                "SELECT COUNT(*) FROM facilities WHERE status = 'active' AND deleted_at IS NULL"
            )
            stats["total_facilities"] = facilities_count.scalar() or 0
        except Exception as e:
            logger.warning(f"Failed to count facilities: {e}")
            stats["total_facilities"] = 0
        
        # Count users
        try:
            users_count = await db.execute(
                "SELECT COUNT(*) FROM users WHERE is_active = true"
            )
            stats["total_users"] = users_count.scalar() or 0
        except Exception as e:
            logger.warning(f"Failed to count users: {e}")
            stats["total_users"] = 0
        
        # Get recent transactions (last 7 days)
        try:
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_transactions = await db.execute(
                "SELECT COUNT(*) FROM transactions WHERE created_at >= :date",
                {"date": seven_days_ago}
            )
            stats["recent_transactions"] = recent_transactions.scalar() or 0
        except Exception as e:
            logger.warning(f"Failed to count recent transactions: {e}")
            stats["recent_transactions"] = 0
        
        # Get total transaction amount (last 30 days)
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            total_amount_result = await db.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE created_at >= :date AND status = 'completed'",
                {"date": thirty_days_ago}
            )
            stats["total_transaction_amount"] = float(total_amount_result.scalar() or 0)
        except Exception as e:
            logger.warning(f"Failed to sum transaction amounts: {e}")
            stats["total_transaction_amount"] = 0.0
        
        # Get pending approvals count
        try:
            pending_approvals = await db.execute(
                "SELECT COUNT(*) FROM facilities WHERE status = 'pending' AND deleted_at IS NULL"
            )
            stats["pending_approvals"] = pending_approvals.scalar() or 0
        except Exception as e:
            logger.warning(f"Failed to count pending approvals: {e}")
            stats["pending_approvals"] = 0
        
        # Add timestamp
        stats["last_updated"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "data": stats,
            "message": "Dashboard statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error while fetching dashboard statistics",
                "message": "Please try again later"
            }
        )


@router.get("/facilities/summary")
async def get_facilities_summary(db: AsyncSession = Depends(get_db)):
    """
    Get facilities summary statistics
    """
    try:
        stats = {}
        
        # Count by status
        try:
            status_counts = await db.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM facilities 
                WHERE deleted_at IS NULL 
                GROUP BY status
                """
            )
            stats["by_status"] = {row["status"]: row["count"] for row in status_counts.fetchall()}
        except Exception as e:
            logger.warning(f"Failed to get facilities by status: {e}")
            stats["by_status"] = {}
        
        # Count by type
        try:
            type_counts = await db.execute(
                """
                SELECT type, COUNT(*) as count 
                FROM facilities 
                WHERE deleted_at IS NULL 
                GROUP BY type
                """
            )
            stats["by_type"] = {row["type"]: row["count"] for row in type_counts.fetchall()}
        except Exception as e:
            logger.warning(f"Failed to get facilities by type: {e}")
            stats["by_type"] = {}
        
        return {
            "success": True,
            "data": stats,
            "message": "Facilities summary retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve facilities summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error while fetching facilities summary",
                "message": "Please try again later"
            }
        )


@router.get("/customers/summary")
async def get_customers_summary(db: AsyncSession = Depends(get_db)):
    """
    Get customers summary statistics
    """
    try:
        stats = {}
        
        # Count by status
        try:
            status_counts = await db.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM customers 
                WHERE deleted_at IS NULL 
                GROUP BY status
                """
            )
            stats["by_status"] = {row["status"]: row["count"] for row in status_counts.fetchall()}
        except Exception as e:
            logger.warning(f"Failed to get customers by status: {e}")
            stats["by_status"] = {}
        
        # Count by customer type
        try:
            type_counts = await db.execute(
                """
                SELECT customer_type, COUNT(*) as count 
                FROM customers 
                WHERE deleted_at IS NULL 
                GROUP BY customer_type
                """
            )
            stats["by_type"] = {row["customer_type"]: row["count"] for row in type_counts.fetchall()}
        except Exception as e:
            logger.warning(f"Failed to get customers by type: {e}")
            stats["by_type"] = {}
        
        return {
            "success": True,
            "data": stats,
            "message": "Customers summary retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve customers summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error while fetching customers summary",
                "message": "Please try again later"
            }
        )