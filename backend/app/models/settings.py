"""
Settings Models
مدل‌های تنظیمات سیستم و کاربر
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, generate_short_id


class SettingType(str, Enum):
    """نوع تنظیم"""
    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    JSON = "json"
    LIST = "list"


class SystemSetting(Base, TimestampMixin):
    """
    مدل تنظیمات سیستم
    تنظیمات سراسری قابل تغییر از پنل ادمین
    """
    __tablename__ = "system_settings"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("SET-"))

    # کلید و مقدار
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(SQLEnum(SettingType), default=SettingType.STRING, nullable=False)

    # توضیحات
    label = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)

    # محدودیت‌ها
    min_value = Column(String(50), nullable=True)
    max_value = Column(String(50), nullable=True)
    allowed_values = Column(JSON, nullable=True)  # لیست مقادیر مجاز
    regex_pattern = Column(String(255), nullable=True)

    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)
    is_editable = Column(Boolean, default=True, nullable=False)  # برخی تنظیمات فقط از کد قابل تغییرند
    requires_restart = Column(Boolean, default=False)

    # امنیت
    is_sensitive = Column(Boolean, default=False)  # برای رمزهای عبور و API Keys
    is_encrypted = Column(Boolean, default=False)

    # ترتیب نمایش
    display_order = Column(String(50), default="100")

    def get_typed_value(self):
        """دریافت مقدار با نوع صحیح"""
        if self.value is None:
            return None

        if self.value_type == SettingType.INTEGER:
            return int(self.value)
        elif self.value_type == SettingType.FLOAT:
            return float(self.value)
        elif self.value_type == SettingType.BOOLEAN:
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == SettingType.JSON:
            import json
            return json.loads(self.value)
        elif self.value_type == SettingType.LIST:
            return [v.strip() for v in self.value.split(",")]
        return self.value

    def __repr__(self):
        return f"<SystemSetting {self.key}>"


class UserSetting(Base, TimestampMixin):
    """
    مدل تنظیمات کاربر
    تنظیمات شخصی هر کاربر
    """
    __tablename__ = "user_settings"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("UST-"))
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # کلید و مقدار
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(SQLEnum(SettingType), default=SettingType.STRING, nullable=False)

    # توضیحات
    label = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)

    # روابط
    user = relationship("User", back_populates="user_settings")

    class Meta:
        unique_together = [("user_id", "key")]

    def get_typed_value(self):
        """دریافت مقدار با نوع صحیح"""
        if self.value is None:
            return None

        if self.value_type == SettingType.INTEGER:
            return int(self.value)
        elif self.value_type == SettingType.FLOAT:
            return float(self.value)
        elif self.value_type == SettingType.BOOLEAN:
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == SettingType.JSON:
            import json
            return json.loads(self.value)
        elif self.value_type == SettingType.LIST:
            return [v.strip() for v in self.value.split(",")]
        return self.value

    def __repr__(self):
        return f"<UserSetting {self.user_id}:{self.key}>"


# تنظیمات پیش‌فرض سیستم
DEFAULT_SYSTEM_SETTINGS = [
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
        "description": "Number of days before expiry to show warning",
        "category": "alerts"
    },
    {
        "key": "profile_completion_minimum",
        "value": "70",
        "value_type": "int",
        "label": "Minimum Profile Completion",
        "description": "Minimum percentage for profile completion",
        "category": "profile"
    },
    {
        "key": "kyc_validity_years",
        "value": "2",
        "value_type": "int",
        "label": "KYC Validity Period (Years)",
        "description": "Number of years KYC is valid",
        "category": "kyc"
    },
    {
        "key": "default_ai_provider",
        "value": "openai",
        "value_type": "string",
        "label": "Default AI Provider",
        "description": "Default AI provider (openai, anthropic, google)",
        "category": "ai",
        "allowed_values": ["openai", "anthropic", "google"]
    },
    {
        "key": "ai_enabled",
        "value": "true",
        "value_type": "bool",
        "label": "AI Features Enabled",
        "description": "Enable or disable AI features",
        "category": "ai"
    },
    {
        "key": "google_drive_sync_enabled",
        "value": "false",
        "value_type": "bool",
        "label": "Google Drive Sync",
        "description": "Enable automatic sync to Google Drive",
        "category": "sync"
    },
    {
        "key": "auto_save_interval",
        "value": "30",
        "value_type": "int",
        "label": "Auto Save Interval (seconds)",
        "description": "Interval for automatic saving",
        "category": "general"
    },
    {
        "key": "session_timeout_minutes",
        "value": "30",
        "value_type": "int",
        "label": "Session Timeout (minutes)",
        "description": "Session timeout duration",
        "category": "security"
    },
    {
        "key": "max_login_attempts",
        "value": "5",
        "value_type": "int",
        "label": "Max Login Attempts",
        "description": "Maximum failed login attempts before lockout",
        "category": "security"
    },
]

# تنظیمات پیش‌فرض کاربر
DEFAULT_USER_SETTINGS = [
    {
        "key": "theme",
        "value": "light",
        "value_type": "string",
        "label": "Theme",
        "category": "appearance"
    },
    {
        "key": "language",
        "value": "en",
        "value_type": "string",
        "label": "Language",
        "category": "appearance"
    },
    {
        "key": "notifications_enabled",
        "value": "true",
        "value_type": "bool",
        "label": "Notifications",
        "category": "notifications"
    },
    {
        "key": "email_notifications",
        "value": "true",
        "value_type": "bool",
        "label": "Email Notifications",
        "category": "notifications"
    },
    {
        "key": "dashboard_widgets",
        "value": '["pending_tasks", "expiring_docs", "recent_activity"]',
        "value_type": "json",
        "label": "Dashboard Widgets",
        "category": "dashboard"
    },
]
