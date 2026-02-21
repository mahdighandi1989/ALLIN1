from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200))
    account_type = Column(SQLEnum(AccountType), default=AccountType.RETAIL)
    status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.ACTIVE)
    email = Column(String(100))
    phone = Column(String(50))
    mobile = Column(String(50))
    address = Column(Text)
    branch = Column(String(100))
    relationship_manager = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    facilities = relationship("Facility", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', account_no='{self.account_no}')>"