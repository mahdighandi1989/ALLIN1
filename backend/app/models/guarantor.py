"""
Guarantor Models
مدل‌های ضامن و چک‌های ضمانت
"""
from datetime import date
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Numeric
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class Guarantor(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل ضامن
    هر تسهیلات می‌تواند تا 6 ضامن داشته باشد
    """
    __tablename__ = "guarantors"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("GNT-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(50), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True)

    # اطلاعات ضامن
    guarantor_name = Column(String(255), nullable=False)
    guarantor_name_ar = Column(String(255), nullable=True)
    relationship_type = Column(String(100), nullable=True)  # Director, Partner, Third Party, etc.

    # مدارک
    passport_no = Column(String(50), nullable=True)
    passport_expiry = Column(Date, nullable=True)
    emirates_id = Column(String(20), nullable=True)
    emirates_id_expiry = Column(Date, nullable=True)

    # اطلاعات تماس
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    # اطلاعات مالی
    net_worth = Column(Numeric(18, 2), nullable=True)
    annual_income = Column(Numeric(15, 2), nullable=True)
    employer = Column(String(255), nullable=True)

    # ضمانت
    guarantee_amount = Column(Numeric(18, 2), nullable=True)
    guarantee_date = Column(Date, nullable=True)
    guarantee_expiry = Column(Date, nullable=True)
    guarantee_type = Column(String(50), default="Personal")  # Personal, Corporate

    # وضعیت
    is_active = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verification_date = Column(Date, nullable=True)

    # یادداشت
    notes = Column(Text, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="guarantors")
    facility = relationship("Facility", back_populates="guarantors")
    cheques = relationship("GuarantorCheque", back_populates="guarantor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Guarantor {self.id}: {self.guarantor_name}>"


class GuarantorCheque(Base, TimestampMixin, AuditMixin):
    """
    مدل چک ضمانت
    هر ضامن می‌تواند چندین چک ضمانت داشته باشد
    """
    __tablename__ = "guarantor_cheques"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("CHQ-"))
    guarantor_id = Column(String(50), ForeignKey("guarantors.id", ondelete="CASCADE"), nullable=False, index=True)

    # اطلاعات چک
    cheque_no = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=True)
    branch = Column(String(100), nullable=True)
    account_no = Column(String(50), nullable=True)

    # مبلغ و تاریخ
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default="AED")
    cheque_date = Column(Date, nullable=True)

    # وضعیت
    status = Column(String(50), default="Held")  # Held, Returned, Deposited, Cleared
    status_date = Column(Date, nullable=True)
    status_notes = Column(Text, nullable=True)

    # یادداشت
    notes = Column(Text, nullable=True)

    # روابط
    guarantor = relationship("Guarantor", back_populates="cheques")

    def __repr__(self):
        return f"<GuarantorCheque {self.cheque_no}: {self.amount}>"
