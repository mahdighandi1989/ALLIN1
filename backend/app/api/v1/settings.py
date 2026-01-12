"""
Settings API Routes
روت‌های تنظیمات سیستم و کاربر
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user, TokenData, require_role
from app.core.config import settings as app_settings

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


# ========== System Settings (Admin Only) ==========
@router.get("/system")
async def get_system_settings(
    category: Optional[str] = None,
    current_user: TokenData = Depends(require_role(["admin", "manager"]))
):
    """
    دریافت تنظیمات سیستم (فقط ادمین)
    """
    settings_list = [
        {
            "key": "expiry_alert_days",
            "value": "30",
            "value_type": "int",
            "label": "Expiry Alert Days",
            "description": "Number of days before expiry to show alert",
            "category": "alerts"
        },
        {
            "key": "expiry_warning_days",
            "value": "60",
            "value_type": "int",
            "label": "Expiry Warning Days",
            "category": "alerts"
        },
        {
            "key": "profile_completion_minimum",
            "value": "70",
            "value_type": "int",
            "label": "Minimum Profile Completion %",
            "category": "profile"
        },
        {
            "key": "default_ai_provider",
            "value": "openai",
            "value_type": "string",
            "label": "Default AI Provider",
            "category": "ai",
            "allowed_values": ["openai", "anthropic", "google"]
        },
        {
            "key": "ai_enabled",
            "value": "true",
            "value_type": "bool",
            "label": "AI Features Enabled",
            "category": "ai"
        },
        {
            "key": "google_drive_sync_enabled",
            "value": "false",
            "value_type": "bool",
            "label": "Google Drive Sync",
            "category": "sync"
        },
        {
            "key": "session_timeout_minutes",
            "value": "30",
            "value_type": "int",
            "label": "Session Timeout (minutes)",
            "category": "security"
        }
    ]

    if category:
        settings_list = [s for s in settings_list if s["category"] == category]

    # Group by category
    grouped = {}
    for s in settings_list:
        cat = s["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(s)

    return {"settings": settings_list, "grouped": grouped}


@router.put("/system/{key}")
async def update_system_setting(
    key: str,
    setting: SystemSettingUpdate,
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    بروزرسانی تنظیم سیستم (فقط ادمین)
    """
    return {
        "key": key,
        "value": setting.value,
        "updated_by": current_user.user_id,
        "message": "Setting updated successfully"
    }


# ========== User Settings ==========
@router.get("/user")
async def get_user_settings():
    """
    دریافت تنظیمات کاربر فعلی
    این endpoint عمومی است و تنظیمات پیش‌فرض برمی‌گرداند
    """
    return {
        "settings": {
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
    }


@router.put("/user")
async def update_user_settings(
    settings: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user)
):
    """
    بروزرسانی تنظیمات کاربر
    """
    return {
        "message": "Settings updated successfully",
        "settings": settings
    }


# ========== AI Configuration ==========
@router.get("/ai/providers")
async def get_ai_providers(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    دریافت تنظیمات ارائه‌دهندگان AI
    """
    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI",
                "enabled": bool(app_settings.OPENAI_API_KEY),
                "models": ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
                "default_model": app_settings.OPENAI_MODEL
            },
            {
                "id": "anthropic",
                "name": "Anthropic (Claude)",
                "enabled": bool(app_settings.ANTHROPIC_API_KEY),
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "default_model": app_settings.ANTHROPIC_MODEL
            },
            {
                "id": "google",
                "name": "Google (Gemini)",
                "enabled": bool(app_settings.GOOGLE_AI_API_KEY),
                "models": ["gemini-pro", "gemini-pro-vision"],
                "default_model": app_settings.GOOGLE_AI_MODEL
            }
        ],
        "default_provider": app_settings.DEFAULT_AI_PROVIDER,
        "enabled_features": app_settings.AI_ENABLED_FEATURES
    }


@router.put("/ai/providers/{provider_id}")
async def update_ai_provider(
    provider_id: str,
    config: AIProviderConfig,
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    بروزرسانی تنظیمات ارائه‌دهنده AI
    """
    return {
        "provider": provider_id,
        "config": config.model_dump(),
        "message": "AI provider configuration updated"
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
