"""
Deposit Models
مدل‌های سپرده و FD
"""
from datetime import date
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Numeric, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class DepositType(str, Enum):
    """نوع سپرده"""
    FIXED_DEPOSIT = "FD"  # سپرده ثابت
    SAVINGS = "Savings"  # پس‌انداز
    CURRENT = "Current"  # جاری
    CALL_DEPOSIT = "Call"  # سپرده دیداری


class DepositStatus(str, Enum):
    """وضعیت سپرده"""
    ACTIVE = "Active"
    MATURED = "Matured"
    CLOSED = "Closed"
    UNDER_LIEN = "Under Lien"


class Deposit(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل سپرده
    شامل انواع سپرده‌ها و FD
    """
    __tablename__ = "deposits"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("DEP-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # اطلاعات سپرده
    deposit_type = Column(SQLEnum(DepositType), default=DepositType.FIXED_DEPOSIT, nullable=False)
    deposit_number = Column(String(50), nullable=False, unique=True)
    account_number = Column(String(50), nullable=True)
    status = Column(SQLEnum(DepositStatus), default=DepositStatus.ACTIVE, nullable=False)

    # مبلغ
    principal_amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default="AED")
    maturity_amount = Column(Numeric(18, 2), nullable=True)

    # نرخ و شرایط
    interest_rate = Column(Numeric(5, 2), nullable=True)
    tenor_days = Column(Integer, nullable=True)
    tenor_months = Column(Integer, nullable=True)

    # تاریخ‌ها
    opening_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=True)
    last_renewal_date = Column(Date, nullable=True)
    closure_date = Column(Date, nullable=True)

    # رهن
    is_under_lien = Column(Boolean, default=False)
    lien_amount = Column(Numeric(18, 2), nullable=True)
    lien_reference = Column(String(100), nullable=True)
    lien_facility_id = Column(String(50), nullable=True)  # ارتباط با تسهیلات

    # Auto Renewal
    auto_renewal = Column(Boolean, default=False)
    renewal_count = Column(Integer, default=0)

    # یادداشت
    notes = Column(Text, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="deposits")

    @property
    def days_to_maturity(self):
        """روزهای باقیمانده تا سررسید"""
        if self.maturity_date:
            return (self.maturity_date - date.today()).days
        return None

    @property
    def available_amount(self):
        """مبلغ آزاد (بدون رهن)"""
        if self.is_under_lien and self.lien_amount:
            return max(0, float(self.principal_amount) - float(self.lien_amount))
        return float(self.principal_amount)

    def __repr__(self):
        return f"<Deposit {self.deposit_number}: {self.principal_amount} {self.currency}>"
