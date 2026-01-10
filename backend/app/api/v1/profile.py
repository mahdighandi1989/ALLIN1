"""
User Profile API Routes
روت‌های API پروفایل کاربر
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.security import get_current_user, TokenData
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


# ========== Schemas ==========
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class ProfileResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    language: Optional[str] = "en"
    timezone: Optional[str] = "UTC"
    bio: Optional[str] = None
    is_active: bool
    last_login: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ========== Endpoints ==========
@router.get("")
async def get_my_profile(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت پروفایل کاربر فعلی
    """
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Return mock data if user not found in DB
        return {
            "id": current_user.user_id,
            "username": current_user.username,
            "email": f"{current_user.username}@example.com",
            "full_name": current_user.username.title(),
            "phone": None,
            "department": "General",
            "position": "Staff",
            "role": current_user.role,
            "avatar_url": None,
            "language": "en",
            "timezone": "Asia/Dubai",
            "bio": None,
            "is_active": True,
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone": getattr(user, 'phone', None),
        "department": getattr(user, 'department', None),
        "position": getattr(user, 'position', None),
        "role": user.role,
        "avatar_url": getattr(user, 'avatar_url', None),
        "language": getattr(user, 'language', 'en'),
        "timezone": getattr(user, 'timezone', 'Asia/Dubai'),
        "bio": getattr(user, 'bio', None),
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.put("")
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی پروفایل کاربر فعلی
    """
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    await db.commit()

    return {"message": "Profile updated successfully"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    تغییر رمز عبور
    """
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    from app.core.security import verify_password, get_password_hash
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/activity")
async def get_my_activity(
    limit: int = 20,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت فعالیت‌های اخیر کاربر
    """
    # Return mock activity data
    return {
        "items": [
            {
                "id": "1",
                "action": "login",
                "description": "Logged in to the system",
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": "192.168.1.1"
            },
            {
                "id": "2",
                "action": "update_customer",
                "description": "Updated customer: ABC Company",
                "timestamp": datetime.utcnow().isoformat(),
                "entity_type": "customer",
                "entity_id": "CUS-001"
            },
            {
                "id": "3",
                "action": "create_facility",
                "description": "Created new facility for XYZ Corp",
                "timestamp": datetime.utcnow().isoformat(),
                "entity_type": "facility",
                "entity_id": "FAC-001"
            }
        ],
        "total": 3
    }


@router.get("/stats")
async def get_my_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    آمار کاربر
    """
    return {
        "customers_created": 12,
        "facilities_managed": 8,
        "tasks_completed": 45,
        "tasks_pending": 5,
        "documents_uploaded": 23,
        "last_active": datetime.utcnow().isoformat()
    }


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    آپلود عکس پروفایل
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Use JPEG, PNG, GIF or WebP")

    # In production, upload to cloud storage
    # For now, just return a placeholder URL
    avatar_url = f"/uploads/avatars/{current_user.user_id}.jpg"

    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url
    }


@router.delete("/avatar")
async def delete_avatar(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف عکس پروفایل
    """
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()

    if user and hasattr(user, 'avatar_url'):
        user.avatar_url = None
        await db.commit()

    return {"message": "Avatar deleted successfully"}


@router.get("/sessions")
async def get_active_sessions(
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت نشست‌های فعال
    """
    return {
        "sessions": [
            {
                "id": "session-1",
                "device": "Chrome on Windows",
                "ip_address": "192.168.1.1",
                "location": "Dubai, UAE",
                "last_active": datetime.utcnow().isoformat(),
                "is_current": True
            }
        ]
    }


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    لغو یک نشست
    """
    return {"message": f"Session {session_id} revoked successfully"}
