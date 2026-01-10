"""
Security Record Model
مدل لیست اوراق بهادار سالانه
"""
from enum import Enum
from sqlalchemy import Column, String, Text, ForeignKey, Date, Integer, Numeric, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_short_id


class SecurityRecordCategory(str, Enum):
    """دسته‌بندی اوراق"""
    RETAIL = "Retail"
    CORPORATE = "Corporate"


class SecurityRecord(Base, TimestampMixin, SoftDeleteMixin):
    """
    رکوردهای سالانه اوراق بهادار
    از فایل‌های Securities List 2022-2026
    """
    __tablename__ = "security_records"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("SECR-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    account_no = Column(String(50), index=True)

    year = Column(Integer, nullable=False, index=True)
    category = Column(SQLEnum(SecurityRecordCategory), nullable=False, index=True)

    entry_date = Column(Date)
    row_no = Column(Integer)
    branch = Column(String(20))
    customer_name = Column(String(255))

    # FD Info
    fd_number = Column(String(100))
    fd_amount = Column(Numeric(18, 2))
    fd_currency = Column(String(10))

    # Guarantor Info
    guarantor_name = Column(String(255))
    guarantor_account = Column(String(50))

    # Cheque Info
    cheque_no = Column(String(50))
    cheque_amount = Column(Numeric(18, 2))
    cheque_bank = Column(String(100))
    cheque_currency = Column(String(10), default="AED")

    # Undertakings
    undertaking_127 = Column(Boolean, default=False)
    undertaking_128 = Column(Boolean, default=False)

    remarks = Column(Text)
    source_file = Column(String(255))
    source_sheet = Column(String(100))

    # Relationship
    customer = relationship("Customer", back_populates="security_records")

    def __repr__(self):
        return f"<SecurityRecord {self.year}/{self.category.value}: {self.account_no}>"
