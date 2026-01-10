"""
Document Model
مدل مدارک و اسناد مشتری
"""
from enum import Enum
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_short_id


class DocumentType(str, Enum):
    """انواع مدارک"""
    TRADE_LICENSE = "TradeLicense"
    PASSPORT = "Passport"
    EMIRATES_ID = "EmiratesID"
    VISA = "Visa"
    TENANCY = "Tenancy"
    COMMERCIAL_REGISTER = "CommercialRegister"
    MOA = "MOA"  # Memorandum of Association
    POA = "POA"  # Power of Attorney
    OTHER = "Other"


class DocumentStatus(str, Enum):
    """وضعیت مدرک"""
    VALID = "Valid"
    EXPIRED = "Expired"
    EXPIRING_SOON = "ExpiringSoon"
    PENDING = "Pending"
    REJECTED = "Rejected"


class Document(Base, TimestampMixin, SoftDeleteMixin):
    """
    مدارک مشتریان
    همه مدارک در یک جدول نرمالایز شده
    """
    __tablename__ = "documents"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("DOC-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    document_no = Column(String(100), index=True)

    issue_date = Column(Date)
    expiry_date = Column(Date, index=True)

    # Additional fields based on document type
    nationality = Column(String(100))  # For Passport
    address = Column(Text)  # For Tenancy
    visa_type = Column(String(100))  # For Visa
    is_golden = Column(Boolean, default=False)  # For Emirates ID

    remarks = Column(Text)
    file_path = Column(String(500))

    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.VALID)

    # Relationship
    customer = relationship("Customer", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.document_type.value}: {self.document_no}>"
