"""Facility Model"""
from datetime import date
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


def generate_id():
    return "F" + str(uuid.uuid4())[:7].upper()


class FacilityType(str, enum.Enum):
    LOAN = "loan"
    OVERDRAFT = "overdraft"
    LC = "lc"
    LG = "lg"
    OTHER = "other"


class FacilityStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"
    DEFAULTED = "defaulted"


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(8), primary_key=True, default=generate_id)
    customer_id = Column(String(8), ForeignKey("customers.id"), nullable=False, index=True)

    # Basic info
    facility_type = Column(SQLEnum(FacilityType), nullable=False)
    name = Column(String(200))
    status = Column(SQLEnum(FacilityStatus), default=FacilityStatus.ACTIVE)

    # Amounts
    amount = Column(Numeric(18, 2), nullable=False)
    outstanding = Column(Numeric(18, 2), default=0)
    currency = Column(String(10), default="AED")

    # Dates
    start_date = Column(Date)
    expiry_date = Column(Date)

    # Terms
    interest_rate = Column(Numeric(5, 2))
    tenor_months = Column(String(20))

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    customer = relationship("Customer", back_populates="facilities")
