"""Runtime, editable key/value system settings (stored in the DB).

Unlike env-based config (read-only at runtime), these can be changed by an admin
from the Settings page and take effect immediately. Values are stored as text.
"""
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"


# Editable settings with their defaults + a short description for the UI.
EDITABLE_SETTINGS = {
    "app_name": {"default": "ALLIN1 Banking Operations", "label": "Application name", "type": "text"},
    "default_currency": {"default": "AED", "label": "Default currency", "type": "text"},
    "expiry_warning_days": {"default": "30", "label": "Expiry warning window (days)", "type": "number"},
    "dashboard_recent_limit": {"default": "5", "label": "Recent items on dashboard", "type": "number"},
}
