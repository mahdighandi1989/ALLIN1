"""
Facility Models
مدل‌های تسهیلات بانکی - شامل انواع مختلف تسهیلات
"""
from datetime import date
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Numeric, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class FacilityType(str, Enum):
    """انواع تسهیلات"""
    OD = "OD"  # Overdraft - اضافه برداشت
    LOAN = "Loan"  # وام
    CHQ_DISC = "ChqDisc"  # تنزیل چک
    LG = "LG"  # Letter of Guarantee - ضمانت‌نامه
    TR = "TR"  # Trust Receipt - حواله
    LC_SIGHT = "LC_Sight"  # اعتبار اسنادی دیداری
    LC_USANCE = "LC_Usance"  # اعتبار اسنادی یوزانس
    LOG = "LoG"  # Loan on Gold - وام طلا
    CREDIT_CARD = "CreditCard"  # کارت اعتباری
    OTHER = "Other"


class FacilityStatus(str, Enum):
    """وضعیت تسهیلات"""
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"
    DEFAULTED = "defaulted"
    RESTRUCTURED = "restructured"


class Facility(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل تسهیلات
    هر تسهیلات شامل اطلاعات کامل از نوع، مبلغ، وثایق و ...
    """
    __tablename__ = "facilities"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("FAC-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # اطلاعات پایه
    facility_type = Column(SQLEnum(FacilityType), nullable=False)
    facility_name = Column(String(200), nullable=True)
    reference_no = Column(String(100), nullable=True)
    status = Column(SQLEnum(FacilityStatus), default=FacilityStatus.ACTIVE, nullable=False)

    # مبالغ
    approved_amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default="AED")
    utilized_amount = Column(Numeric(18, 2), default=0)
    outstanding_amount = Column(Numeric(18, 2), default=0)
    available_amount = Column(Numeric(18, 2), nullable=True)

    # تاریخ‌ها
    sanction_date = Column(Date, nullable=True)
    disbursement_date = Column(Date, nullable=True)
    maturity_date = Column(Date, nullable=True)
    last_renewal_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)

    # نرخ و شرایط
    interest_rate = Column(Numeric(5, 2), nullable=True)
    margin = Column(Numeric(5, 2), nullable=True)
    tenor_months = Column(Integer, nullable=True)
    repayment_frequency = Column(String(50), nullable=True)  # Monthly, Quarterly, etc.
    installment_amount = Column(Numeric(15, 2), nullable=True)

    # اطلاعات تکمیلی برای هر نوع تسهیلات
    # Overdraft
    od_limit = Column(Numeric(18, 2), nullable=True)
    od_review_date = Column(Date, nullable=True)

    # Loan
    loan_purpose = Column(Text, nullable=True)
    loan_type = Column(String(50), nullable=True)  # Term, Revolving, etc.

    # Letter of Guarantee
    lg_beneficiary = Column(String(255), nullable=True)
    lg_type = Column(String(50), nullable=True)  # Bid Bond, Performance, etc.
    lg_purpose = Column(Text, nullable=True)

    # LC
    lc_type = Column(String(50), nullable=True)  # Import, Export
    lc_beneficiary = Column(String(255), nullable=True)
    lc_tenor_days = Column(Integer, nullable=True)

    # وثایق مرتبط
    security_type = Column(String(100), nullable=True)
    security_value = Column(Numeric(18, 2), nullable=True)
    security_description = Column(Text, nullable=True)
    lien_amount = Column(Numeric(18, 2), nullable=True)
    lien_reference = Column(String(100), nullable=True)

    # چک‌های ضمانت
    borrower_cheques = Column(JSON, default=list)
    # ساختار: [{"cheque_no": "", "amount": 0, "date": "", "bank": ""}, ...]

    # مستندات و شرایط
    sanction_conditions = Column(JSON, default=list)
    covenants = Column(JSON, default=list)
    documents_required = Column(JSON, default=list)

    # یادداشت‌ها
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)
    ai_risk_assessment = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="facilities")
    guarantors = relationship("Guarantor", back_populates="facility", cascade="all, delete-orphan")
    checklists = relationship("Checklist", back_populates="facility", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="facility")

    @property
    def utilization_percentage(self) -> float:
        """درصد استفاده از تسهیلات"""
        if self.approved_amount and self.approved_amount > 0:
            return float(self.utilized_amount or 0) / float(self.approved_amount) * 100
        return 0

    @property
    def is_overdue(self) -> bool:
        """بررسی سررسید"""
        if self.maturity_date:
            return date.today() > self.maturity_date
        return False

    @property
    def days_to_maturity(self) -> Optional[int]:
        """روزهای باقیمانده تا سررسید"""
        if self.maturity_date:
            return (self.maturity_date - date.today()).days
        return None

    def calculate_available(self):
        """محاسبه مبلغ قابل استفاده"""
        self.available_amount = (self.approved_amount or 0) - (self.utilized_amount or 0)

    def __repr__(self):
        return f"<Facility {self.id}: {self.facility_type.value} - {self.approved_amount}>"
