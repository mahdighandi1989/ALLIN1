"""
Checklist Models
مدل‌های چک‌لیست و تسک‌ها
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class ChecklistStatus(str, Enum):
    """وضعیت چک‌لیست"""
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class TaskStatus(str, Enum):
    """وضعیت تسک"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ON_HOLD = "On Hold"


class TaskPriority(str, Enum):
    """اولویت تسک"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Checklist(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل چک‌لیست اصلی
    هر چک‌لیست مرتبط با یک مشتری و/یا تسهیلات
    """
    __tablename__ = "checklists"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("CKL-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(50), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True)

    # اطلاعات چک‌لیست
    checklist_type = Column(String(100), nullable=False)  # Regulatory, Facility, KYC, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ChecklistStatus), default=ChecklistStatus.DRAFT, nullable=False)

    # تاریخ‌ها
    due_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)

    # پیشرفت
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    progress_percentage = Column(Integer, default=0)

    # تخصیص
    assigned_to = Column(String(50), nullable=True)  # User ID
    assigned_by = Column(String(50), nullable=True)

    # یادداشت
    notes = Column(Text, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="checklists")
    facility = relationship("Facility", back_populates="checklists")
    items = relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")
    tasks = relationship("ChecklistTask", back_populates="checklist", cascade="all, delete-orphan")

    def calculate_progress(self):
        """محاسبه پیشرفت"""
        if self.total_items > 0:
            self.progress_percentage = int((self.completed_items / self.total_items) * 100)
        else:
            self.progress_percentage = 0

    def __repr__(self):
        return f"<Checklist {self.id}: {self.title}>"


class ChecklistItem(Base, TimestampMixin, AuditMixin):
    """
    مدل آیتم چک‌لیست
    هر آیتم یک مورد قابل تیک زدن
    """
    __tablename__ = "checklist_items"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("CLI-"))
    checklist_id = Column(String(50), ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False, index=True)

    # اطلاعات آیتم
    item_code = Column(String(50), nullable=True)  # کد مرجع
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    order = Column(Integer, default=0)

    # وضعیت
    is_completed = Column(Boolean, default=False)
    is_required = Column(Boolean, default=True)
    is_applicable = Column(Boolean, default=True)  # N/A

    # تاریخ
    completed_date = Column(Date, nullable=True)
    completed_by = Column(String(50), nullable=True)
    due_date = Column(Date, nullable=True)

    # مستند مرتبط
    document_required = Column(Boolean, default=False)
    document_uploaded = Column(Boolean, default=False)
    document_reference = Column(String(255), nullable=True)

    # یادداشت
    notes = Column(Text, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    checklist = relationship("Checklist", back_populates="items")

    def __repr__(self):
        return f"<ChecklistItem {self.id}: {self.title}>"


class ChecklistTask(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل تسک شخصی
    تسک‌های سفارشی اضافه شده به چک‌لیست
    """
    __tablename__ = "checklist_tasks"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("TSK-"))
    checklist_id = Column(String(50), ForeignKey("checklists.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True)

    # اطلاعات تسک
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)

    # تاریخ‌ها
    due_date = Column(Date, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    reminder_date = Column(DateTime(timezone=True), nullable=True)

    # تخصیص
    assigned_to = Column(String(50), nullable=True)
    assigned_by = Column(String(50), nullable=True)

    # پیگیری
    follow_up_count = Column(Integer, default=0)
    last_follow_up = Column(DateTime(timezone=True), nullable=True)

    # یادداشت
    notes = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)

    # متادیتا
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)

    # روابط
    checklist = relationship("Checklist", back_populates="tasks")

    @property
    def is_overdue(self) -> bool:
        """بررسی تاخیر"""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return date.today() > self.due_date
        return False

    @property
    def days_overdue(self):
        """روزهای تاخیر"""
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0

    def __repr__(self):
        return f"<ChecklistTask {self.id}: {self.title}>"
