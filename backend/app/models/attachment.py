"""
Attachment Models
مدل‌های پیوست و فایل
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer,
    ForeignKey, Text, JSON, BigInteger
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class Attachment(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل پیوست
    برای ذخیره فایل‌های پیوست شده به مشتری، تسهیلات و سایر موارد
    """
    __tablename__ = "attachments"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("ATT-"))

    # ارتباطات
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True)
    facility_id = Column(String(50), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    checklist_item_id = Column(String(50), nullable=True, index=True)

    # اطلاعات فایل
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_extension = Column(String(20), nullable=True)
    file_size = Column(BigInteger, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)

    # دسته‌بندی
    category = Column(String(100), nullable=True)  # Document, Image, Report, etc.
    document_type = Column(String(100), nullable=True)  # Trade License, Passport, etc.
    description = Column(Text, nullable=True)

    # ذخیره ابری
    cloud_url = Column(String(500), nullable=True)
    cloud_provider = Column(String(50), nullable=True)  # google_drive, s3, etc.
    cloud_file_id = Column(String(255), nullable=True)

    # نسخه
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    parent_id = Column(String(50), nullable=True)  # برای نسخه‌های قبلی

    # تایید
    verified = Column(Boolean, default=False)
    verified_by = Column(String(50), nullable=True)
    verified_date = Column(DateTime(timezone=True), nullable=True)

    # یادداشت
    notes = Column(Text, nullable=True)

    # متادیتا
    metadata = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="attachments")
    facility = relationship("Facility", back_populates="attachments")

    @property
    def file_size_formatted(self) -> str:
        """اندازه فایل به صورت خوانا"""
        if not self.file_size:
            return "Unknown"
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def __repr__(self):
        return f"<Attachment {self.id}: {self.original_name}>"
