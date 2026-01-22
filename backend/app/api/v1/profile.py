"""
Profile API
API پروفایل کاربر
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import get_current_user, TokenData, verify_password, get_password_hash
from app.core.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.facility import Facility

router = APIRouter()


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("/")
async def get_profile(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "permissions": user.permissions or [],
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.put("/")
async def update_profile(
    data: ProfileUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.email is not None:
        # Check if email is taken
        existing = await db.execute(
            select(User).where(User.email == data.email, User.id != user.id)
        )
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = data.email

    await db.commit()
    await db.refresh(user)

    return {"message": "Profile updated successfully"}


@router.get("/stats")
async def get_profile_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics"""
    # Count customers created by user
    customers_count = (await db.execute(
        select(func.count()).select_from(Customer).where(
            Customer.created_by == current_user.user_id,
            Customer.is_deleted == False
        )
    )).scalar() or 0

    # Count facilities created by user
    facilities_count = (await db.execute(
        select(func.count()).select_from(Facility).where(
            Facility.created_by == current_user.user_id,
            Facility.is_deleted == False
        )
    )).scalar() or 0

    return {
        "customers_created": customers_count,
        "facilities_created": facilities_count,
        "total_actions": customers_count + facilities_count
    }


@router.get("/activity")
async def get_activity(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent activity"""
    # Get recent customers
    recent_customers = await db.execute(
        select(Customer)
        .where(Customer.created_by == current_user.user_id)
        .order_by(Customer.created_at.desc())
        .limit(5)
    )

    # Get recent facilities
    recent_facilities = await db.execute(
        select(Facility)
        .where(Facility.created_by == current_user.user_id)
        .order_by(Facility.created_at.desc())
        .limit(5)
    )

    activities = []

    for c in recent_customers.scalars():
        activities.append({
            "type": "customer",
            "action": "created",
            "description": f"Created customer {c.customer_name}",
            "timestamp": c.created_at.isoformat() if c.created_at else None
        })

    for f in recent_facilities.scalars():
        activities.append({
            "type": "facility",
            "action": "created",
            "description": f"Created facility {f.facility_type.value if hasattr(f.facility_type, 'value') else f.facility_type}",
            "timestamp": f.created_at.isoformat() if f.created_at else None
        })

    # Sort by timestamp
    activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)

    return {"activities": activities[:10]}


@router.get("/sessions")
async def get_sessions(current_user: TokenData = Depends(get_current_user)):
    """Get active sessions (placeholder)"""
    return {
        "sessions": [
            {
                "id": "current",
                "device": "Current Session",
                "ip": "N/A",
                "last_active": datetime.utcnow().isoformat(),
                "is_current": True
            }
        ]
    }


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password"""
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.hashed_password = get_password_hash(data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Revoke a session (placeholder)"""
    if session_id == "current":
        raise HTTPException(status_code=400, detail="Cannot revoke current session")

    return {"message": "Session revoked successfully"}
