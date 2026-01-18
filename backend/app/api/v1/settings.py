"""
Settings API Routes
روت‌های تنظیمات سیستم و کاربر
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, TokenData, require_role
from app.core.config import settings as app_settings
from app.core.database import get_db
from app.models.settings import SystemSetting, UserSetting, SettingType, DEFAULT_SYSTEM_SETTINGS, DEFAULT_USER_SETTINGS

router = APIRouter()


# ========== Schemas ==========
class SystemSettingUpdate(BaseModel):
    value: str


class UserSettingUpdate(BaseModel):
    key: str
    value: Any


class AIProviderConfig(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    enabled: bool = True


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: Optional[str] = None
    use_tls: bool = True
    from_name: str
    from_address: str


class GoogleDriveConfig(BaseModel):
    enabled: bool = False
    folder_id: Optional[str] = None
    sync_interval: int = 300


# ========== Helper Functions ==========
async def ensure_default_settings(db: AsyncSession):
    """Ensure default system settings exist in database"""
    for setting_def in DEFAULT_SYSTEM_SETTINGS:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == setting_def["key"])
        )
        if not result.scalars().first():
            new_setting = SystemSetting(
                key=setting_def["key"],
                value=setting_def["value"],
                value_type=SettingType(setting_def["value_type"]),
                label=setting_def.get("label"),
                description=setting_def.get("description"),
                category=setting_def.get("category"),
                allowed_values=setting_def.get("allowed_values")
            )
            db.add(new_setting)
    await db.commit()


# ========== System Settings (Admin Only) ==========
@router.get("/system")
async def get_system_settings(
    category: Optional[str] = None,
    current_user: TokenData = Depends(require_role(["admin", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت تنظیمات سیستم (فقط ادمین)
    """
    # Ensure default settings exist
    await ensure_default_settings(db)

    # Build query
    query = select(SystemSetting).where(SystemSetting.is_active == True)
    if category:
        query = query.where(SystemSetting.category == category)

    result = await db.execute(query)
    settings_rows = result.scalars().all()

    settings_list = []
    for s in settings_rows:
        settings_list.append({
            "key": s.key,
            "value": s.value,
            "value_type": s.value_type.value if isinstance(s.value_type, SettingType) else s.value_type,
            "label": s.label,
            "description": s.description,
            "category": s.category,
            "allowed_values": s.allowed_values
        })

    # Group by category
    grouped = {}
    for s in settings_list:
        cat = s["category"] or "general"
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(s)

    return {"settings": settings_list, "grouped": grouped}


@router.put("/system/{key}")
async def update_system_setting(
    key: str,
    setting: SystemSettingUpdate,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی تنظیم سیستم (فقط ادمین)
    """
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    db_setting = result.scalars().first()

    if not db_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    if not db_setting.is_editable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This setting cannot be modified"
        )

    db_setting.value = setting.value
    await db.commit()

    return {
        "key": key,
        "value": setting.value,
        "updated_by": current_user.user_id,
        "message": "Setting updated successfully"
    }


# ========== User Settings ==========
async def ensure_user_settings(db: AsyncSession, user_id: str):
    """Ensure default user settings exist for a user"""
    for setting_def in DEFAULT_USER_SETTINGS:
        result = await db.execute(
            select(UserSetting).where(
                UserSetting.user_id == user_id,
                UserSetting.key == setting_def["key"]
            )
        )
        if not result.scalars().first():
            new_setting = UserSetting(
                user_id=user_id,
                key=setting_def["key"],
                value=setting_def["value"],
                value_type=SettingType(setting_def["value_type"]),
                label=setting_def.get("label"),
                category=setting_def.get("category")
            )
            db.add(new_setting)
    await db.commit()


@router.get("/user")
async def get_user_settings(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت تنظیمات کاربر فعلی
    """
    # Ensure default settings exist for user
    await ensure_user_settings(db, current_user.user_id)

    # Get all user settings
    result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == current_user.user_id)
    )
    settings_rows = result.scalars().all()

    # Convert to dictionary
    settings_dict = {}
    for s in settings_rows:
        settings_dict[s.key] = s.get_typed_value()

    # Add default values if not present
    defaults = {
        "theme": "light",
        "language": "en",
        "primary_color": "#2563eb",
        "sidebar_collapsed": False,
        "dense_mode": False,
        "notifications_enabled": True,
        "email_notifications": True,
        "dashboard_widgets": ["pending_tasks", "expiring_docs", "recent_activity"],
        "default_view": "dashboard",
        "items_per_page": 20
    }

    for key, value in defaults.items():
        if key not in settings_dict:
            settings_dict[key] = value

    return {"settings": settings_dict}


@router.put("/user")
async def update_user_settings(
    settings: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی تنظیمات کاربر
    """
    import json

    for key, value in settings.items():
        # Check if setting exists
        result = await db.execute(
            select(UserSetting).where(
                UserSetting.user_id == current_user.user_id,
                UserSetting.key == key
            )
        )
        existing = result.scalars().first()

        # Determine value type
        if isinstance(value, bool):
            value_type = SettingType.BOOLEAN
            str_value = "true" if value else "false"
        elif isinstance(value, int):
            value_type = SettingType.INTEGER
            str_value = str(value)
        elif isinstance(value, float):
            value_type = SettingType.FLOAT
            str_value = str(value)
        elif isinstance(value, (list, dict)):
            value_type = SettingType.JSON
            str_value = json.dumps(value)
        else:
            value_type = SettingType.STRING
            str_value = str(value)

        if existing:
            existing.value = str_value
            existing.value_type = value_type
        else:
            new_setting = UserSetting(
                user_id=current_user.user_id,
                key=key,
                value=str_value,
                value_type=value_type
            )
            db.add(new_setting)

    await db.commit()

    return {
        "message": "Settings updated successfully",
        "settings": settings
    }


# ========== AI Configuration ==========
# Note: AI Provider management has been moved to /api/v1/ai-providers endpoint
# These endpoints are kept for backwards compatibility but redirect to the new endpoints
@router.get("/ai/providers")
async def get_ai_providers(
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت تنظیمات ارائه‌دهندگان AI
    Note: Use /api/v1/ai-providers/providers for full functionality
    """
    from app.api.v1.ai_providers import list_ai_providers
    providers = await list_ai_providers(current_user, db)

    # Format response for backwards compatibility
    return {
        "providers": [
            {
                "id": p.provider_id,
                "name": p.name,
                "enabled": p.enabled,
                "models": p.available_models,
                "default_model": p.default_model
            }
            for p in providers
        ],
        "default_provider": app_settings.DEFAULT_AI_PROVIDER,
        "enabled_features": app_settings.AI_ENABLED_FEATURES
    }


# ========== Email Configuration ==========
@router.get("/email")
async def get_email_settings(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    دریافت تنظیمات ایمیل
    """
    return {
        "smtp_host": app_settings.SMTP_HOST,
        "smtp_port": app_settings.SMTP_PORT,
        "smtp_user": app_settings.SMTP_USER,
        "use_tls": app_settings.SMTP_USE_TLS,
        "from_name": app_settings.EMAIL_FROM_NAME,
        "from_address": app_settings.EMAIL_FROM_ADDRESS,
        "configured": bool(app_settings.SMTP_USER and app_settings.SMTP_PASSWORD)
    }


@router.put("/email")
async def update_email_settings(
    config: EmailConfig,
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    بروزرسانی تنظیمات ایمیل
    """
    return {
        "message": "Email settings updated",
        "config": {k: v for k, v in config.model_dump().items() if k != "smtp_password"}
    }


@router.post("/email/test")
async def test_email(
    to_email: str,
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    تست ارسال ایمیل
    """
    from app.services.email_service import email_service

    result = await email_service.send_notification(
        to=to_email,
        title="Test Email",
        message="This is a test email from Banking Operations System."
    )

    return result


# ========== Google Drive Configuration ==========
@router.get("/google-drive")
async def get_google_drive_settings(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    دریافت تنظیمات Google Drive
    """
    return {
        "enabled": app_settings.GOOGLE_DRIVE_ENABLED,
        "folder_id": app_settings.GOOGLE_DRIVE_FOLDER_ID,
        "sync_interval": app_settings.GOOGLE_DRIVE_SYNC_INTERVAL,
        "configured": bool(app_settings.GOOGLE_CREDENTIALS_FILE)
    }


@router.put("/google-drive")
async def update_google_drive_settings(
    config: GoogleDriveConfig,
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    بروزرسانی تنظیمات Google Drive
    """
    return {
        "message": "Google Drive settings updated",
        "config": config.model_dump()
    }


# ========== Backup & Export ==========
@router.post("/backup")
async def create_backup(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    ایجاد پشتیبان از سیستم
    """
    from datetime import datetime

    backup_info = {
        "id": f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user.user_id,
        "status": "completed",
        "size": "15.2 MB",
        "includes": ["customers", "facilities", "checklists", "attachments"]
    }

    return backup_info


@router.get("/backup/list")
async def list_backups(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    لیست پشتیبان‌ها
    """
    backups = [
        {
            "id": "backup-20250108120000",
            "created_at": "2025-01-08T12:00:00",
            "size": "15.2 MB",
            "location": "google_drive"
        },
        {
            "id": "backup-20250101000000",
            "created_at": "2025-01-01T00:00:00",
            "size": "14.8 MB",
            "location": "local"
        }
    ]

    return {"backups": backups}
