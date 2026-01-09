"""
Note Models
مدل‌های یادداشت و یادآوری
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class NoteCategory(str, Enum):
    """دسته‌بندی یادداشت"""
    GENERAL = "General"
    FOLLOW_UP = "Follow Up"
    MEETING = "Meeting"
    CALL = "Call"
    EMAIL = "Email"
    DOCUMENT = "Document"
    RISK = "Risk"
    COMPLIANCE = "Compliance"
    OTHER = "Other"


class NotePriority(str, Enum):
    """اولویت یادداشت"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ReminderStatus(str, Enum):
    """وضعیت یادآوری"""
    PENDING = "Pending"
    SENT = "Sent"
    DISMISSED = "Dismissed"
    SNOOZED = "Snoozed"


class Note(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل یادداشت مرتبط با مشتری
    """
    __tablename__ = "notes"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("NOT-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # محتوا
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    category = Column(SQLEnum(NoteCategory), default=NoteCategory.GENERAL, nullable=False)
    priority = Column(SQLEnum(NotePriority), default=NotePriority.MEDIUM, nullable=False)

    # یادآوری
    has_reminder = Column(Boolean, default=False)
    reminder_date = Column(DateTime(timezone=True), nullable=True)
    reminder_sent = Column(Boolean, default=False)

    # ارسال ایمیل
    email_sent = Column(Boolean, default=False)
    email_sent_date = Column(DateTime(timezone=True), nullable=True)

    # برچسب‌ها
    tags = Column(JSON, default=list)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="notes_rel")

    def __repr__(self):
        return f"<Note {self.id}: {self.title or self.content[:30]}>"


class PersonalNote(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل یادداشت شخصی کاربر
    این یادداشت‌ها به کاربر تعلق دارند نه به مشتری
    """
    __tablename__ = "personal_notes"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("PNT-"))
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # محتوا
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    category = Column(SQLEnum(NoteCategory), default=NoteCategory.GENERAL, nullable=False)
    priority = Column(SQLEnum(NotePriority), default=NotePriority.MEDIUM, nullable=False)

    # Todo
    is_todo = Column(Boolean, default=False)
    is_done = Column(Boolean, default=False)
    done_date = Column(DateTime(timezone=True), nullable=True)

    # یادآوری
    has_reminder = Column(Boolean, default=False)
    reminder_date = Column(DateTime(timezone=True), nullable=True)
    reminder_sent = Column(Boolean, default=False)

    # ارسال به ایمیل شخصی
    email_sent = Column(Boolean, default=False)
    email_sent_date = Column(DateTime(timezone=True), nullable=True)
    send_to_email = Column(Boolean, default=False)

    # رنگ و نمایش
    color = Column(String(20), default="#ffffff")
    pinned = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)

    # برچسب‌ها
    tags = Column(JSON, default=list)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    user = relationship("User", back_populates="personal_notes")

    def __repr__(self):
        return f"<PersonalNote {self.id}: {self.title or self.content[:30]}>"


class Reminder(Base, TimestampMixin, AuditMixin):
    """
    مدل یادآوری
    """
    __tablename__ = "reminders"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("RMD-"))
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # محتوا
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # زمان
    reminder_time = Column(DateTime(timezone=True), nullable=False)
    repeat_type = Column(String(50), nullable=True)  # None, Daily, Weekly, Monthly
    repeat_end_date = Column(Date, nullable=True)

    # وضعیت
    status = Column(SQLEnum(ReminderStatus), default=ReminderStatus.PENDING, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    snooze_until = Column(DateTime(timezone=True), nullable=True)

    # اعلان
    notification_type = Column(String(50), default="both")  # email, push, both
    email_sent = Column(Boolean, default=False)
    push_sent = Column(Boolean, default=False)

    # ارتباط با موجودیت‌ها (اختیاری)
    related_entity_type = Column(String(50), nullable=True)  # customer, facility, task
    related_entity_id = Column(String(50), nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    def __repr__(self):
        return f"<Reminder {self.id}: {self.title}>"
