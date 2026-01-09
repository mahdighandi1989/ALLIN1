"""
Journal Models
مدل‌های ژورنال و لاگ فعالیت
"""
from sqlalchemy import (
    Column, String, DateTime, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_short_id


class JournalEntry(Base):
    """
    مدل ژورنال فعالیت‌ها
    ثبت تمام فعالیت‌های سیستم به صورت تاریخچه
    """
    __tablename__ = "journal_entries"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("JRN-"))
    user_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # زمان
    timestamp = Column(DateTime(timezone=True), nullable=False)

    # نوع عملیات
    action_type = Column(String(100), nullable=False)  # create, update, delete, view, export, etc.
    entity_type = Column(String(100), nullable=False)  # customer, facility, checklist, etc.
    entity_id = Column(String(50), nullable=True, index=True)

    # توضیحات
    description = Column(Text, nullable=True)
    details = Column(JSON, default=dict)

    # تغییرات
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # اطلاعات سیستمی
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(50), nullable=True)

    # روابط
    user = relationship("User", back_populates="journal_entries")

    def __repr__(self):
        return f"<JournalEntry {self.id}: {self.action_type} on {self.entity_type}>"
