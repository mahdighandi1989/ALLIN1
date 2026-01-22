"""
Settings API
API تنظیمات
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.core.security import get_current_user, TokenData, require_role
from app.core.database import get_db
from app.models.settings import SystemSetting, UserSetting, SettingType

router = APIRouter()


class SettingUpdate(BaseModel):
    value: Any


# Default system settings
DEFAULT_SYSTEM_SETTINGS = [
    {"key": "app_name", "value": "Banking Operations", "type": "string", "category": "general"},
    {"key": "default_currency", "value": "AED", "type": "string", "category": "general"},
    {"key": "expiry_alert_days", "value": "30", "type": "integer", "category": "alerts"},
    {"key": "expiry_warning_days", "value": "60", "type": "integer", "category": "alerts"},
    {"key": "ai_enabled", "value": "true", "type": "boolean", "category": "ai"},
    {"key": "backup_enabled", "value": "true", "type": "boolean", "category": "backup"},
]


async def ensure_defaults(db: AsyncSession):
    """Ensure default settings exist"""
    for setting in DEFAULT_SYSTEM_SETTINGS:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == setting["key"])
        )
        if not result.scalars().first():
            new = SystemSetting(
                key=setting["key"],
                value=setting["value"],
                value_type=SettingType(setting["type"]),
                category=setting["category"]
            )
            db.add(new)
    await db.commit()


@router.get("/system")
async def get_system_settings(
    category: Optional[str] = None,
    current_user: TokenData = Depends(require_role(["admin", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Get system settings"""
    await ensure_defaults(db)

    query = select(SystemSetting).where(SystemSetting.is_active == True)
    if category:
        query = query.where(SystemSetting.category == category)

    result = await db.execute(query)
    settings = result.scalars().all()

    return {
        "settings": [
            {
                "key": s.key,
                "value": s.get_typed_value(),
                "type": s.value_type.value,
                "category": s.category
            }
            for s in settings
        ]
    }


@router.put("/system/{key}")
async def update_system_setting(
    key: str,
    data: SettingUpdate,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Update system setting"""
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalars().first()

    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    # Convert value to string
    if isinstance(data.value, bool):
        setting.value = "true" if data.value else "false"
    elif isinstance(data.value, (list, dict)):
        setting.value = json.dumps(data.value)
    else:
        setting.value = str(data.value)

    await db.commit()
    return {"key": key, "value": setting.get_typed_value(), "message": "Updated successfully"}


@router.get("/user")
async def get_user_settings(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user settings"""
    result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == current_user.user_id)
    )
    settings = result.scalars().all()

    # Build settings dict with defaults
    settings_dict = {
        "theme": "light",
        "language": "en",
        "sidebar_collapsed": False,
        "notifications_enabled": True,
        "items_per_page": 20
    }

    for s in settings:
        settings_dict[s.key] = s.get_typed_value()

    return {"settings": settings_dict}


@router.put("/user")
async def update_user_settings(
    data: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user settings"""
    for key, value in data.items():
        result = await db.execute(
            select(UserSetting).where(
                UserSetting.user_id == current_user.user_id,
                UserSetting.key == key
            )
        )
        setting = result.scalars().first()

        # Determine type
        if isinstance(value, bool):
            value_type = SettingType.BOOLEAN
            str_value = "true" if value else "false"
        elif isinstance(value, int):
            value_type = SettingType.INTEGER
            str_value = str(value)
        elif isinstance(value, (list, dict)):
            value_type = SettingType.JSON
            str_value = json.dumps(value)
        else:
            value_type = SettingType.STRING
            str_value = str(value)

        if setting:
            setting.value = str_value
            setting.value_type = value_type
        else:
            new = UserSetting(
                user_id=current_user.user_id,
                key=key,
                value=str_value,
                value_type=value_type
            )
            db.add(new)

    await db.commit()
    return {"message": "Settings updated successfully"}
