"""
User Models
مدل‌های کاربر و احراز هویت
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum
import uuid

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid


class UserRole(str, Enum):
    """نقش‌های کاربری"""
    ADMIN = "admin"
    MANAGER = "manager"
    OFFICER = "officer"
    VIEWER = "viewer"


class User(Base, TimestampMixin, SoftDeleteMixin):
    """مدل کاربر"""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # اطلاعات شخصی
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # نقش و دسترسی
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    permissions = Column(JSON, default=list)
    department = Column(String(100), nullable=True)
    branch = Column(String(100), nullable=True)

    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # امنیت
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # تنظیمات شخصی
    preferences = Column(JSON, default=dict)
    notification_settings = Column(JSON, default=dict)

    # تنظیمات ایمیل شخصی
    personal_email = Column(String(255), nullable=True)
    email_notifications_enabled = Column(Boolean, default=True)

    # روابط
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    personal_notes = relationship("PersonalNote", back_populates="user", cascade="all, delete-orphan")
    user_settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user")

    @property
    def display_name(self) -> str:
        if self.full_name:
            return self.full_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def has_permission(self, permission: str) -> bool:
        """بررسی دسترسی"""
        if self.is_superuser or self.role == UserRole.ADMIN:
            return True
        if "*" in self.permissions:
            return True
        return permission in self.permissions

    def __repr__(self):
        return f"<User {self.username}>"


class UserSession(Base, TimestampMixin):
    """مدل نشست کاربر"""
    __tablename__ = "user_sessions"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # توکن
    access_token = Column(String(500), nullable=False, unique=True)
    refresh_token = Column(String(500), nullable=True)

    # اطلاعات دستگاه
    device_info = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # زمان
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=True)

    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # روابط
    user = relationship("User", back_populates="sessions")

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<UserSession {self.id[:8]}>"
