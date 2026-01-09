"""
KYC Models
مدل‌های شناسایی مشتری (KYC)
"""
from datetime import date
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Numeric, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class KYCStatus(str, Enum):
    """وضعیت KYC"""
    PENDING = "Pending"
    COMPLETE = "Complete"
    EXPIRED = "Expired"
    REVIEW_REQUIRED = "Review Required"


class KYCRiskLevel(str, Enum):
    """سطح ریسک KYC"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    PROHIBITED = "Prohibited"


class KYCRecord(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل KYC
    اطلاعات کامل شناسایی مشتری
    """
    __tablename__ = "kyc_records"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("KYC-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # وضعیت
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.PENDING, nullable=False)
    risk_level = Column(SQLEnum(KYCRiskLevel), default=KYCRiskLevel.LOW, nullable=False)

    # تاریخ‌ها
    kyc_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)

    # اطلاعات فردی (برای Retail)
    date_of_birth = Column(Date, nullable=True)
    place_of_birth = Column(String(100), nullable=True)
    nationality = Column(String(100), nullable=True)
    occupation = Column(String(100), nullable=True)
    employer_name = Column(String(255), nullable=True)
    employer_address = Column(Text, nullable=True)
    monthly_income = Column(Numeric(15, 2), nullable=True)
    source_of_income = Column(String(255), nullable=True)
    source_of_wealth = Column(Text, nullable=True)

    # اطلاعات شرکتی (برای Corporate)
    nature_of_business = Column(String(255), nullable=True)
    business_activities = Column(Text, nullable=True)
    annual_turnover = Column(Numeric(18, 2), nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    countries_of_operation = Column(JSON, default=list)

    # UBO - Ultimate Beneficial Owner
    ubo_details = Column(JSON, default=list)
    # ساختار: [{"name": "", "nationality": "", "share": 0, "pep": false}, ...]

    # PEP - Politically Exposed Person
    is_pep = Column(Boolean, default=False)
    pep_details = Column(Text, nullable=True)

    # Sanctions
    sanctions_check = Column(Boolean, default=False)
    sanctions_check_date = Column(Date, nullable=True)
    sanctions_result = Column(String(100), nullable=True)

    # مستندات جمع‌آوری شده
    documents_collected = Column(JSON, default=list)
    # ساختار: [{"type": "", "number": "", "expiry": "", "verified": false}, ...]

    # سوالات و پاسخ‌های KYC
    kyc_questionnaire = Column(JSON, default=dict)

    # تایید
    verified_by = Column(String(100), nullable=True)
    verified_date = Column(Date, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_date = Column(Date, nullable=True)

    # یادداشت‌ها
    notes = Column(Text, nullable=True)
    risk_notes = Column(Text, nullable=True)

    # تحلیل هوش مصنوعی
    ai_analysis = Column(JSON, default=dict)
    ai_risk_score = Column(Integer, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="kyc_records")

    @property
    def is_expired(self) -> bool:
        """بررسی انقضا"""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False

    @property
    def days_to_expiry(self):
        """روزهای باقیمانده تا انقضا"""
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return None

    def get_status_color(self) -> str:
        """رنگ وضعیت"""
        if self.status == KYCStatus.COMPLETE and not self.is_expired:
            return "green"
        elif self.status == KYCStatus.EXPIRED or self.is_expired:
            return "red"
        elif self.status == KYCStatus.REVIEW_REQUIRED:
            return "orange"
        return "yellow"

    def __repr__(self):
        return f"<KYCRecord {self.id}: {self.status.value}>"
