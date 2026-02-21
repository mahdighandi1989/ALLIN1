from sqlalchemy import Column, Integer, String, Numeric, Date, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class FacilityType(str, enum.Enum):
    LOAN = "loan"
    OVERDRAFT = "overdraft"
    LC = "lc"
    GUARANTEE = "guarantee"
    OTHER = "other"


class FacilityStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"
    DEFAULTED = "defaulted"
    WRITTEN_OFF = "written_off"


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(33), primary_key=True, index=True)
    customer_id = Column(String(33), ForeignKey("customers.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    facility_type = Column(Enum(FacilityType), default=FacilityType.LOAN)
    start_date = Column(Date)
    end_date = Column(Date)
    expiry_date = Column(Date)
    outstanding = Column(Numeric(15, 2), default=0)
    status = Column(Enum(FacilityStatus), default=FacilityStatus.ACTIVE)
    purpose = Column(String(500))
    interest_rate = Column(Numeric(5, 2))
    collateral_value = Column(Numeric(15, 2))
    risk_rating = Column(String(10))
    relationship_manager = Column(String(255))
    branch = Column(String(100))
    approved_by = Column(String(255))
    approved_date = Column(Date)
    reviewed_date = Column(Date)
    next_review_date = Column(Date)
    comments = Column(String(1000))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="facilities")

    def __repr__(self):
        return f"<Facility(id={self.id}, amount={self.amount})>"


# برای backward compatibility
__all__ = ["Facility", "FacilityType", "FacilityStatus"]