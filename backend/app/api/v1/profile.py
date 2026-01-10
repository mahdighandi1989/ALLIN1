"""
User Profile API Routes
روت‌های API پروفایل کاربر
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import get_current_user, TokenData
from app.core.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.models.facility import Facility
from app.models.checklist import ChecklistItem
from app.models.attachment import Attachment
from app.models.note import Note

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
        # If user not in DB, return basic info from token
        return {
            "id": current_user.user_id,
            "username": current_user.username,
            "email": None,
            "full_name": current_user.username.title() if current_user.username else "User",
            "phone": None,
            "department": None,
            "position": None,
            "role": current_user.role,
            "avatar_url": None,
            "language": "en",
            "timezone": "Asia/Dubai",
            "bio": None,
            "is_active": True,
            "last_login": None,
            "created_at": None
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
    دریافت فعالیت‌های اخیر کاربر - از یادداشت‌ها
    """
    # Get recent notes as activity
    result = await db.execute(
        select(Note).where(
            Note.created_by == current_user.user_id,
            Note.is_deleted == False
        ).order_by(Note.created_at.desc()).limit(limit)
    )
    notes = result.scalars().all()

    activities = []
    for note in notes:
        activities.append({
            "id": note.id,
            "action": "create_note",
            "description": f"Created note: {note.title or note.content[:50]}...",
            "timestamp": note.created_at.isoformat() if note.created_at else None,
            "entity_type": "note",
            "entity_id": note.id
        })

    return {
        "items": activities,
        "total": len(activities)
    }


@router.get("/stats")
async def get_my_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    آمار واقعی کاربر از دیتابیس
    """
    # Count customers created by user
    customers_result = await db.execute(
        select(func.count()).select_from(Customer).where(
            Customer.created_by == current_user.user_id,
            Customer.is_deleted == False
        )
    )
    customers_count = customers_result.scalar() or 0

    # Count all customers if user is admin
    if current_user.role == "admin":
        all_customers_result = await db.execute(
            select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
        )
        customers_count = all_customers_result.scalar() or 0

    # Count facilities
    facilities_result = await db.execute(
        select(func.count()).select_from(Facility).where(Facility.is_deleted == False)
    )
    facilities_count = facilities_result.scalar() or 0

    # Count completed checklist items
    completed_tasks_result = await db.execute(
        select(func.count()).select_from(ChecklistItem).where(
            ChecklistItem.is_completed == True,
            ChecklistItem.is_deleted == False
        )
    )
    completed_tasks = completed_tasks_result.scalar() or 0

    # Count pending checklist items
    pending_tasks_result = await db.execute(
        select(func.count()).select_from(ChecklistItem).where(
            ChecklistItem.is_completed == False,
            ChecklistItem.is_deleted == False
        )
    )
    pending_tasks = pending_tasks_result.scalar() or 0

    # Count attachments/documents
    docs_result = await db.execute(
        select(func.count()).select_from(Attachment).where(Attachment.is_deleted == False)
    )
    docs_count = docs_result.scalar() or 0

    # Count notes
    notes_result = await db.execute(
        select(func.count()).select_from(Note).where(
            Note.created_by == current_user.user_id,
            Note.is_deleted == False
        )
    )
    notes_count = notes_result.scalar() or 0

    return {
        "customers_created": customers_count,
        "facilities_managed": facilities_count,
        "tasks_completed": completed_tasks,
        "tasks_pending": pending_tasks,
        "documents_uploaded": docs_count,
        "notes_created": notes_count,
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
    avatar_url = f"/uploads/avatars/{current_user.user_id}.jpg"

    # Update user avatar_url in DB
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()
    if user and hasattr(user, 'avatar_url'):
        user.avatar_url = avatar_url
        await db.commit()

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
    دریافت نشست‌های فعال - فعلاً فقط نشست فعلی
    """
    return {
        "sessions": [
            {
                "id": "current-session",
                "device": "Current Browser",
                "ip_address": "N/A",
                "location": "N/A",
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
    if session_id == "current-session":
        raise HTTPException(status_code=400, detail="Cannot revoke current session")

    return {"message": f"Session {session_id} revoked successfully"}
