"""Customer Model"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


def generate_customer_id():
    """Generate a unique customer ID with 'C' prefix and full UUID to avoid collisions"""
    return "C" + str(uuid.uuid4()).replace('-', '').upper()


class AccountType(str, enum.Enum):
    RETAIL = "retail"
    CORPORATE = "corporate"
    SME = "sme"


class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(33), primary_key=True, default=generate_customer_id)
    account_no = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200))  # Arabic/Persian name
    account_type = Column(SQLEnum(AccountType), default=AccountType.RETAIL)
    status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.ACTIVE)

    # Contact
    email = Column(String(100))
    phone = Column(String(50))
    mobile = Column(String(50))
    address = Column(Text)

    # Business
    branch = Column(String(100))
    relationship_manager = Column(String(100))

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    facilities = relationship("Facility", back_populates="customer")

    def __repr__(self) -> str:
        """String representation for debugging and logging"""
        return (
            f"<Customer(id='{self.id}', "
            f"account_no='{self.account_no}', "
            f"name='{self.name}', "
            f"type='{self.account_type.value if self.account_type else None}', "
            f"status='{self.status.value if self.status else None}')>"
        )

    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"Customer {self.account_no} - {self.name}"