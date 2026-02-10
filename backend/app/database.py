from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
import logging

from app.database import get_db
from app.models.facility import Facility
from app.models.user import User
from app.models.transaction import Transaction

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get dashboard statistics.
    """
    try:
        # Start a transaction explicitly to handle rollback on error
        await db.begin()
        
        # Total facilities amount - with explicit error handling
        try:
            total_amount_result = await db.execute(select(func.sum(Facility.amount)))
            total_amount = total_amount_result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error calculating total facilities amount: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error while calculating total facilities amount: {str(e)}"
            )
        
        # Total users count
        try:
            total_users_result = await db.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error counting total users: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error while counting users: {str(e)}"
            )
        
        # Total transactions count
        try:
            total_transactions_result = await db.execute(select(func.count(Transaction.id)))
            total_transactions = total_transactions_result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error counting total transactions: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error while counting transactions: {str(e)}"
            )
        
        # Recent transactions (last 5)
        try:
            recent_transactions_result = await db.execute(
                select(Transaction)
                .order_by(Transaction.created_at.desc())
                .limit(5)
            )
            recent_transactions = recent_transactions_result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching recent transactions: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error while fetching recent transactions: {str(e)}"
            )
        
        # Commit the transaction since all queries succeeded
        await db.commit()
        
        return {
            "total_amount": total_amount,
            "total_users": total_users,
            "total_transactions": total_transactions,
            "recent_transactions": [
                {
                    "id": tx.id,
                    "amount": tx.amount,
                    "type": tx.type,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None
                }
                for tx in recent_transactions
            ]
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        # Catch any other SQLAlchemy errors
        logger.error(f"Database transaction error in get_dashboard_stats: {str(e)}")
        # Ensure rollback if still in transaction
        try:
            await db.rollback()
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Database transaction error: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error in get_dashboard_stats: {str(e)}")
        # Ensure rollback if still in transaction
        try:
            await db.rollback()
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )