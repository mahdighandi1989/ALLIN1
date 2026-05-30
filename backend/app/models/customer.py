from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from ..database import Base


def generate_customer_id() -> str:
    """Generate a unique customer ID: a 'C' prefix followed by 32 hex chars."""
    return "C" + uuid.uuid4().hex


class AccountType(str, enum.Enum):
    RETAIL = "retail"
    CORPORATE = "corporate"
    SME = "sme"


class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# Store the enum *value* ("retail") rather than the member NAME ("RETAIL"), so
# the DB matches the API/filter strings the frontend sends and reads back
# correctly. (Without values_callable, SQLAlchemy persists the NAME, which breaks
# every == comparison against a lowercase value and corrupts reads.)
def _enum_col(enum_cls, **kw):
    return Column(
        SQLEnum(enum_cls, values_callable=lambda e: [m.value for m in e]), **kw
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(33), primary_key=True, default=generate_customer_id)
    account_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200))
    account_type = _enum_col(AccountType, default=AccountType.RETAIL)
    status = _enum_col(CustomerStatus, default=CustomerStatus.ACTIVE)
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

    def __init__(self, **kwargs):
        # Apply sensible Python-side defaults at construction time so freshly
        # built (un-flushed) instances already expose them. Column-level
        # ``default=`` only fires on INSERT, which is too late for callers/tests
        # that read these attributes before committing.
        kwargs.setdefault("account_type", AccountType.RETAIL)
        kwargs.setdefault("status", CustomerStatus.ACTIVE)
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', account_no='{self.account_no}')>"