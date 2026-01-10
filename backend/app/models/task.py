"""
Custom Task Models
مدل‌های وظایف سفارشی
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class TaskStatus(str, Enum):
    """وضعیت وظیفه"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ON_HOLD = "On Hold"


class TaskPriority(str, Enum):
    """اولویت وظیفه"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class CustomTask(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل وظایف سفارشی
    برای پیگیری کارها و یادآوری‌ها
    """
    __tablename__ = "custom_tasks"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("TSK-"))

    # ارتباط با مشتری و تسهیلات
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True)
    facility_id = Column(String(50), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    account_no = Column(String(50), nullable=True, index=True)  # شماره حساب برای سازگاری با اکسل

    # اطلاعات وظیفه
    task_id = Column(String(100), nullable=True, unique=True)  # شناسه از اکسل
    task_name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # وضعیت و اولویت
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)

    # تاریخ‌ها
    due_date = Column(Date, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)

    # یادداشت‌ها
    notes = Column(Text, nullable=True)

    # متادیتا
    is_active = Column(Boolean, default=True)
    custom_fields = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", backref="tasks")
    facility = relationship("Facility", backref="tasks")

    def __repr__(self):
        return f"<CustomTask {self.id}: {self.task_name[:30]}>"
