from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import enum
from ..database import Base


class AccountType(str, PyEnum):
    CURRENT = "current"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    LOAN = "loan"


class CustomerStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    account_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    national_id = Column(String(50), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    account_type = Column(Enum(AccountType), default=AccountType.CURRENT)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    credit_limit = Column(Numeric(15, 2), default=0)
    current_balance = Column(Numeric(15, 2), default=0)
    risk_rating = Column(String(10))
    relationship_manager = Column(String(255))
    branch = Column(String(100))
    opened_date = Column(Date)
    last_review_date = Column(Date)
    next_review_date = Column(Date)
    comments = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    facilities = relationship("Facility", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', account_no='{self.account_no}')>"


# این خط برای backward compatibility اضافه شده
__all__ = ["Customer", "AccountType", "CustomerStatus"]