from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class FacilityType(str, enum.Enum):
    """Facility type enumeration"""
    LOAN = "loan"
    OVERDRAFT = "overdraft"
    LC = "lc"
    LG = "lg"
    OTHER = "other"


class FacilityStatus(str, enum.Enum):
    """Facility status enumeration"""
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"
    DEFAULTED = "defaulted"


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=False, index=True)
    facility_type = Column(Enum(FacilityType), nullable=False)
    name = Column(String(200), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    outstanding = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default="AED")
    status = Column(Enum(FacilityStatus), default=FacilityStatus.ACTIVE)
    start_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    interest_rate = Column(Numeric(5, 2), nullable=True)
    tenor_months = Column(String(20), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default='now()')
    updated_at = Column(DateTime, nullable=True, onupdate='now()')
    is_deleted = Column(Boolean, default=False)

    # Relationships
    customer = relationship("Customer", back_populates="facilities")

    def __repr__(self):
        return f"<Facility {self.id}: {self.name} ({self.facility_type})>"
