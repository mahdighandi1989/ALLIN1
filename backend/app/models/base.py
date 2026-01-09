"""
Base Models and Mixins
مدل‌های پایه و Mixin های مشترک
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Boolean, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
import uuid

Base = declarative_base()


class TimestampMixin:
    """Mixin برای افزودن فیلدهای زمانی"""

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )


class SoftDeleteMixin:
    """Mixin برای حذف نرم"""

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def deleted_by(cls):
        return Column(String(50), nullable=True)

    def soft_delete(self, user_id: str = None):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id


class AuditMixin:
    """Mixin برای ردیابی تغییرات"""

    @declared_attr
    def created_by(cls):
        return Column(String(50), nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(String(50), nullable=True)


def generate_uuid():
    """تولید UUID یکتا"""
    return str(uuid.uuid4())


def generate_short_id(prefix: str = "") -> str:
    """تولید ID کوتاه با پیشوند"""
    short_uuid = str(uuid.uuid4())[:8].upper()
    return f"{prefix}{short_uuid}" if prefix else short_uuid
