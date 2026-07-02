"""Offer Letter models — the offer-letter / facility-proposal workflow.

Now wired into the application: registered via ``app.models.__init__``, exposed
through ``app.routers.offer_letters`` and the ``OfferLetter*`` schemas. An offer
letter captures the proposed financial terms for a customer (optionally tied to a
facility); its repayment schedule is generated into ``offer_calculations``.

The Customer/Facility back-references are intentionally omitted (those models do
not declare an ``offer_letters`` relationship); the FK columns preserve the link.
"""
from datetime import date, datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Numeric, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from decimal import Decimal

from app.database import Base
from app.models.enum_utils import TolerantEnum


def generate_offer_id():
    """Generate offer letter ID with OL prefix"""
    return "OL" + str(uuid.uuid4())[:8].upper()


def _enum_col(enum_cls, **kw):
    # Persist the enum *value* ("draft"), not the member NAME ("DRAFT"), so the
    # stored data matches the API strings and == filters work. native_enum=False
    # (plain VARCHAR) + TolerantEnum makes the column resilient to legacy/dirty
    # values on read — same convention as the Customer/Facility models.
    return Column(
        TolerantEnum(
            enum_cls, values_callable=lambda e: [m.value for m in e], native_enum=False
        ),
        **kw,
    )


class OfferStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class CollateralType(str, enum.Enum):
    PROPERTY = "property"
    VEHICLE = "vehicle"
    CASH_DEPOSIT = "cash_deposit"
    GUARANTEE = "guarantee"
    SHARES = "shares"
    OTHER = "other"


class RepaymentType(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    BULLET = "bullet"


class OfferLetter(Base):
    __tablename__ = "offer_letters"

    # id stays "OL"+8 hex for continuity, but the column leaves headroom so the
    # generator can grow without another width migration.
    id = Column(String(36), primary_key=True, default=generate_offer_id)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    # Facility ids are 9 chars ("F"+8 hex) and the column must match
    # facilities.id (String(33)) — the old String(8) overflowed on EVERY real
    # facility id, so no offer letter could ever be linked to a facility.
    facility_id = Column(String(33), ForeignKey("facilities.id"), nullable=True, index=True)
    
    # Basic Information
    offer_date = Column(Date, nullable=False, default=date.today)
    expiry_date = Column(Date, nullable=False)
    status = _enum_col(OfferStatus, default=OfferStatus.DRAFT)
    
    # Financial Terms
    principal_amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default="AED")
    # Rates are stored as PERCENT (8.5 = 8.5%) and the API accepts up to 100,
    # so precision must allow >= 3 integer digits: Numeric(7,4) caps at
    # 999.9999. The old Numeric(5,4) overflowed at 10% — routine SME rates.
    interest_rate = Column(Numeric(7, 4), nullable=False)  # Annual rate (percent)
    profit_rate = Column(Numeric(7, 4))  # For Islamic banking
    tenor_months = Column(Integer, nullable=False)
    grace_period_months = Column(Integer, default=0)
    
    # Repayment Details
    repayment_type = _enum_col(RepaymentType, default=RepaymentType.MONTHLY)
    monthly_installment = Column(Numeric(18, 2))
    total_repayment_amount = Column(Numeric(18, 2))
    
    # Fees and Charges
    processing_fee = Column(Numeric(18, 2), default=0)
    processing_fee_percentage = Column(Numeric(7, 4))
    arrangement_fee = Column(Numeric(18, 2), default=0)
    commitment_fee = Column(Numeric(7, 4))
    early_settlement_fee = Column(Numeric(7, 4))
    late_payment_fee = Column(Numeric(18, 2))
    
    # Security and Collateral
    collateral_type = _enum_col(CollateralType)
    collateral_value = Column(Numeric(18, 2))
    collateral_description = Column(Text)
    guarantee_required = Column(Boolean, default=False)
    guarantee_amount = Column(Numeric(18, 2))
    
    # Terms and Conditions
    purpose_of_facility = Column(String(500))
    special_conditions = Column(Text)
    covenants = Column(Text)
    
    # Approval and Workflow
    prepared_by = Column(String(100))
    reviewed_by = Column(String(100))
    approved_by = Column(String(100))
    approval_date = Column(Date)
    approval_comments = Column(Text)
    
    # Customer Response
    customer_response_date = Column(Date)
    customer_comments = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    
    # Relationships. NOTE: the Customer/Facility back-references are intentionally
    # omitted — those models do not define an ``offer_letters`` relationship, so
    # declaring back_populates here would break mapper configuration if this
    # module were ever imported. The FK columns above preserve the association.
    attachments = relationship("OfferAttachment", back_populates="offer_letter", cascade="all, delete-orphan")
    calculations = relationship("OfferCalculation", back_populates="offer_letter", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<OfferLetter(id='{self.id}', "
            f"customer_id='{self.customer_id}', "
            f"amount={self.principal_amount}, "
            f"status='{self.status.value if self.status else None}')>"
        )


class OfferAttachment(Base):
    __tablename__ = "offer_attachments"
    
    # Full UUIDs: the truncated-uuid PK anti-pattern already bit users.id once
    # (see backend/migrations/versions/003_widen_user_id.py).
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offer_letter_id = Column(String(36), ForeignKey("offer_letters.id"), nullable=False)

    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Metadata
    uploaded_by = Column(String(100))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String(500))
    
    # Relationships
    offer_letter = relationship("OfferLetter", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<OfferAttachment(id='{self.id}', filename='{self.filename}')>"


class OfferCalculation(Base):
    __tablename__ = "offer_calculations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offer_letter_id = Column(String(36), ForeignKey("offer_letters.id"), nullable=False)

    # Calculation Details
    calculation_date = Column(Date, default=date.today)
    installment_number = Column(Integer, nullable=False)
    payment_date = Column(Date, nullable=False)
    
    # Payment Breakdown
    opening_balance = Column(Numeric(18, 2), nullable=False)
    principal_payment = Column(Numeric(18, 2), nullable=False)
    interest_payment = Column(Numeric(18, 2), nullable=False)
    total_payment = Column(Numeric(18, 2), nullable=False)
    closing_balance = Column(Numeric(18, 2), nullable=False)
    
    # Additional Details
    cumulative_principal = Column(Numeric(18, 2))
    cumulative_interest = Column(Numeric(18, 2))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    offer_letter = relationship("OfferLetter", back_populates="calculations")

    def __repr__(self) -> str:
        return (
            f"<OfferCalculation(id='{self.id}', "
            f"offer_id='{self.offer_letter_id}', "
            f"installment={self.installment_number}, "
            f"payment={self.total_payment})>"
        )