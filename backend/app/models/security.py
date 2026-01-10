"""
Security Models
مدل‌های اوراق بهادار و ضمانت‌ها (Securities List)
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Numeric, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class SecurityCategory(str, Enum):
    """دسته‌بندی اوراق"""
    RETAIL = "Retail"
    CORPORATE = "Corporate"


class SecurityStatus(str, Enum):
    """وضعیت"""
    ACTIVE = "Active"
    RELEASED = "Released"
    EXPIRED = "Expired"


class Security(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل اوراق بهادار و ضمانت‌ها
    بر اساس ساختار Securities List
    """
    __tablename__ = "securities"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("SEC-"))

    # ارتباطات
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True)
    account_no = Column(String(50), nullable=True, index=True)

    # اطلاعات پایه
    security_no = Column(Integer, nullable=True)  # شماره ردیف
    branch = Column(String(20), nullable=True)
    customer_name = Column(String(255), nullable=True)
    category = Column(SQLEnum(SecurityCategory), default=SecurityCategory.RETAIL, nullable=False)
    year = Column(Integer, nullable=True)  # سال ثبت
    month = Column(String(50), nullable=True)  # ماه ثبت

    # FD (سپرده ثابت)
    has_fd = Column(Boolean, default=False)
    fd_details = Column(Text, nullable=True)

    # ضامنین
    guarantors = Column(JSON, default=list)  # لیست ضامنین

    # چک‌های ضمانت
    cheque_numbers = Column(JSON, default=list)  # شماره چک‌ها
    issuing_bank = Column(String(100), nullable=True)
    cheque_amount_aed = Column(Numeric(18, 2), nullable=True)
    cheque_amount_other = Column(String(100), nullable=True)  # مبالغ دیگر

    # مستندات
    undertaking_127 = Column(String(50), default="Available")  # Under Taking (127)
    guarantee_128 = Column(String(50), default="Available")  # Guarantee (128)
    credit_facility_agreement = Column(String(50), default="Available")
    original_offer_letter = Column(String(50), default="Available")

    # املاک
    property_no = Column(String(100), nullable=True)
    mortgage_amount_aed = Column(Numeric(18, 2), nullable=True)
    property_location = Column(String(100), nullable=True)  # IRAN, Dubai, etc.

    # Safe Box
    safe_box = Column(String(100), nullable=True)

    # تاریخ‌ها
    stored_date = Column(Date, nullable=True)
    taken_out_date = Column(Date, nullable=True)

    # وضعیت
    status = Column(SQLEnum(SecurityStatus), default=SecurityStatus.ACTIVE, nullable=False)
    remarks = Column(Text, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)
    source_file = Column(String(255), nullable=True)  # فایل منبع

    # روابط
    customer = relationship("Customer", backref="securities")

    def __repr__(self):
        return f"<Security {self.id}: {self.customer_name}>"
