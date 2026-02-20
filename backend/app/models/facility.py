"""Facility Model"""
from datetime import date
from decimal import Decimal
from sqlalchemy import Column, String, Boolean, DateTime, Date, Numeric, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


def generate_facility_id():
    """Generate a unique facility ID with 'F' prefix"""
    return 'F' + str(uuid.uuid4())[:7].upper()


class FacilityType(str, enum.Enum):
    LOAN = "loan"
    CREDIT_FACILITY = "credit_facility"
    GUARANTEE = "guarantee"
    LETTER_OF_CREDIT = "letter_of_credit"
    OVERDRAFT = "overdraft"


class FacilityStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CLOSED = "closed"
    PENDING = "pending"


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(8), primary_key=True, default=generate_facility_id)
    customer_id = Column(String(33), ForeignKey("customers.id"), nullable=False, index=True)
    facility_type = Column(SQLEnum(FacilityType), nullable=False)
    name = Column(String(200), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False, default=0)
    outstanding = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default="AED")
    start_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    end_date = Column(Date)  # For backward compatibility
    interest_rate = Column(Numeric(5, 2))
    tenor_months = Column(String(20))
    status = Column(SQLEnum(FacilityStatus), default=FacilityStatus.ACTIVE)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    customer = relationship("Customer", back_populates="facilities")
    offer_letters = relationship("OfferLetter", back_populates="facility")

    def __repr__(self) -> str:
        return (
            f"<Facility(id='{self.id}', "
            f"customer_id='{self.customer_id}', "
            f"name='{self.name}', "
            f"amount={self.amount}, "
            f"type='{self.facility_type.value if self.facility_type else None}', "
            f"status='{self.status.value if self.status else None}')>"
        )

    def __str__(self) -> str:
        return f"Facility {self.id} - {self.name}"
