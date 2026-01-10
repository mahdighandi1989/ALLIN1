"""
Customer Models
مدل‌های مشتری و پروفایل جامع - بر اساس 290+ فیلد سیستم اکسل
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Numeric, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_uuid


class AccountType(str, Enum):
    """نوع حساب"""
    CORPORATE = "corporate"
    RETAIL = "retail"
    SME = "sme"


class CustomerStatus(str, Enum):
    """وضعیت مشتری"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class Customer(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل اصلی مشتری
    شامل اطلاعات پایه و ارتباط با سایر جداول
    """
    __tablename__ = "customers"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    account_no = Column(String(50), unique=True, nullable=False, index=True)

    # اطلاعات پایه (PF_1-15)
    customer_name = Column(String(255), nullable=False, index=True)
    customer_name_ar = Column(String(255), nullable=True)  # نام به عربی/فارسی
    account_type = Column(SQLEnum(AccountType), default=AccountType.RETAIL, nullable=False)
    branch = Column(String(100), nullable=True)
    relationship_manager = Column(String(100), nullable=True)
    status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.ACTIVE, nullable=False)

    # اطلاعات تماس
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    po_box = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="UAE")

    # اطلاعات شرکتی
    company_type = Column(String(100), nullable=True)  # LLC, Sole Proprietor, etc.
    industry = Column(String(100), nullable=True)
    established_date = Column(Date, nullable=True)
    number_of_employees = Column(Integer, nullable=True)

    # یادداشت‌ها و توضیحات
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # وضعیت تکمیل
    profile_completeness = Column(Integer, default=0)  # درصد تکمیل
    last_review_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)

    # متادیتا
    tags = Column(JSON, default=list)  # برچسب‌ها
    custom_fields = Column(JSON, default=dict)  # فیلدهای سفارشی

    # روابط
    profile = relationship("CustomerProfile", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    facilities = relationship("Facility", back_populates="customer", cascade="all, delete-orphan")
    guarantors = relationship("Guarantor", back_populates="customer", cascade="all, delete-orphan")
    properties = relationship("Property", back_populates="customer", cascade="all, delete-orphan")
    deposits = relationship("Deposit", back_populates="customer", cascade="all, delete-orphan")
    kyc_records = relationship("KYCRecord", back_populates="customer", cascade="all, delete-orphan")
    checklists = relationship("Checklist", back_populates="customer", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="customer", cascade="all, delete-orphan")
    notes_rel = relationship("Note", back_populates="customer", cascade="all, delete-orphan")

    # New relationships for comprehensive schema
    documents = relationship("Document", back_populates="customer", cascade="all, delete-orphan")
    partners = relationship("Partner", back_populates="customer", cascade="all, delete-orphan")
    security_records = relationship("SecurityRecord", back_populates="customer", cascade="all, delete-orphan")
    tasks = relationship("CustomTask", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.account_no}: {self.customer_name}>"


class CustomerProfile(Base, TimestampMixin, AuditMixin):
    """
    پروفایل جامع مشتری
    شامل تمام 290+ فیلد اطلاعاتی بر اساس ساختار اکسل
    """
    __tablename__ = "customer_profiles"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True)

    # ================= مدارک تجاری (PF_16-42) =================
    # Trade License
    trade_license_no = Column(String(100), nullable=True)
    trade_license_issue_date = Column(Date, nullable=True)
    trade_license_expiry_date = Column(Date, nullable=True)
    trade_license_authority = Column(String(100), nullable=True)
    trade_license_activities = Column(Text, nullable=True)

    # Passport
    passport_no = Column(String(50), nullable=True)
    passport_issue_date = Column(Date, nullable=True)
    passport_expiry_date = Column(Date, nullable=True)
    passport_issue_country = Column(String(100), nullable=True)
    nationality = Column(String(100), nullable=True)

    # Emirates ID
    emirates_id_no = Column(String(20), nullable=True)
    emirates_id_issue_date = Column(Date, nullable=True)
    emirates_id_expiry_date = Column(Date, nullable=True)

    # Visa
    visa_no = Column(String(50), nullable=True)
    visa_issue_date = Column(Date, nullable=True)
    visa_expiry_date = Column(Date, nullable=True)
    visa_type = Column(String(50), nullable=True)

    # Tenancy Contract
    tenancy_no = Column(String(50), nullable=True)
    tenancy_start_date = Column(Date, nullable=True)
    tenancy_end_date = Column(Date, nullable=True)
    tenancy_amount = Column(Numeric(15, 2), nullable=True)

    # MOA/AOA
    moa_no = Column(String(50), nullable=True)
    moa_date = Column(Date, nullable=True)

    # ================= شرکا (PF_43-66) =================
    partners = Column(JSON, default=list)
    # ساختار: [{"name": "", "nationality": "", "share": 0, "passport": "", ...}, ...]

    # ================= خلاصه تسهیلات (از PF_67-110) =================
    # این اطلاعات از جدول Facilities محاسبه می‌شوند
    total_facilities_count = Column(Integer, default=0)
    total_facilities_amount = Column(Numeric(18, 2), default=0)
    total_outstanding = Column(Numeric(18, 2), default=0)

    # ================= وثایق (PF_111-160) =================
    # Under Lien
    underlien_aed = Column(Numeric(15, 2), default=0)
    underlien_usd = Column(Numeric(15, 2), default=0)
    underlien_other = Column(Numeric(15, 2), default=0)
    underlien_currency = Column(String(10), nullable=True)

    # Borrower Cheques
    borrower_cheque_no = Column(String(50), nullable=True)
    borrower_cheque_amount = Column(Numeric(15, 2), nullable=True)
    borrower_cheque_date = Column(Date, nullable=True)
    borrower_cheque_bank = Column(String(100), nullable=True)
    borrower_cheques = Column(JSON, default=list)

    # Collateral
    collateral_aed = Column(Numeric(15, 2), default=0)
    collateral_description = Column(Text, nullable=True)

    # ================= مستندات (PF_161-180) =================
    undertaking_127 = Column(Boolean, default=False)
    undertaking_127_date = Column(Date, nullable=True)
    personal_guarantee = Column(Boolean, default=False)
    personal_guarantee_date = Column(Date, nullable=True)

    # پیوست‌ها (لیست نام فایل‌ها)
    attachments_list = Column(JSON, default=list)

    # ================= ردیابی و تاریخچه (PF_181-197) =================
    seclist_entry_date = Column(Date, nullable=True)
    seclist_entry_by = Column(String(100), nullable=True)
    seclist_last_update = Column(DateTime(timezone=True), nullable=True)

    kyc_entry_date = Column(Date, nullable=True)
    kyc_entry_by = Column(String(100), nullable=True)
    kyc_last_update = Column(DateTime(timezone=True), nullable=True)
    kyc_next_review = Column(Date, nullable=True)

    # ================= اطلاعات مالی =================
    annual_turnover = Column(Numeric(18, 2), nullable=True)
    net_worth = Column(Numeric(18, 2), nullable=True)
    monthly_income = Column(Numeric(15, 2), nullable=True)

    # ================= ریسک و امتیازدهی =================
    risk_rating = Column(String(10), nullable=True)  # Low, Medium, High
    credit_score = Column(Integer, nullable=True)
    risk_notes = Column(Text, nullable=True)

    # ================= متادیتا و فیلدهای سفارشی =================
    custom_data = Column(JSON, default=dict)
    ai_analysis = Column(JSON, default=dict)  # تحلیل‌های هوش مصنوعی

    # روابط
    customer = relationship("Customer", back_populates="profile")

    def calculate_completeness(self) -> int:
        """محاسبه درصد تکمیل پروفایل"""
        required_fields = [
            self.trade_license_no, self.trade_license_expiry_date,
            self.passport_no, self.passport_expiry_date,
            self.emirates_id_no, self.emirates_id_expiry_date,
            self.nationality
        ]
        filled = sum(1 for f in required_fields if f is not None)
        return int((filled / len(required_fields)) * 100)

    def get_expiring_documents(self, days: int = 30) -> list:
        """دریافت لیست مدارک در حال انقضا"""
        from datetime import datetime, timedelta

        expiring = []
        threshold = datetime.now().date() + timedelta(days=days)

        doc_dates = [
            ("Trade License", self.trade_license_expiry_date),
            ("Passport", self.passport_expiry_date),
            ("Emirates ID", self.emirates_id_expiry_date),
            ("Visa", self.visa_expiry_date),
            ("Tenancy", self.tenancy_end_date),
        ]

        for doc_name, expiry_date in doc_dates:
            if expiry_date and expiry_date <= threshold:
                expiring.append({
                    "document": doc_name,
                    "expiry_date": expiry_date,
                    "days_remaining": (expiry_date - datetime.now().date()).days
                })

        return sorted(expiring, key=lambda x: x["days_remaining"])

    def __repr__(self):
        return f"<CustomerProfile for {self.customer_id}>"
