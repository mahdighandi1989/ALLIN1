"""
Property Valuation and Insurance Models
مدل ارزیابی و بیمه املاک
"""
from sqlalchemy import Column, String, Text, ForeignKey, Date, Integer, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_short_id


class PropertyValuation(Base, TimestampMixin, SoftDeleteMixin):
    """
    تاریخچه ارزیابی‌های ملک
    """
    __tablename__ = "property_valuations"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("VAL-"))
    property_id = Column(String(50), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)

    valuation_year = Column(Integer, nullable=False, index=True)
    valuation_date = Column(Date)
    value = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default="AED")

    valuator = Column(String(255))
    valuator_company = Column(String(255))
    report_no = Column(String(100))
    report_path = Column(String(500))

    notes = Column(Text)

    # Relationship
    property = relationship("Property", back_populates="valuations")

    def __repr__(self):
        return f"<PropertyValuation {self.valuation_year}: {self.value} {self.currency}>"


class PropertyInsurance(Base, TimestampMixin, SoftDeleteMixin):
    """
    بیمه‌نامه‌های ملک
    """
    __tablename__ = "property_insurances"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("INS-"))
    property_id = Column(String(50), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)

    policy_no = Column(String(100), index=True)
    issue_date = Column(Date)
    expiry_date = Column(Date, index=True)

    coverage_amount = Column(Numeric(18, 2))
    premium = Column(Numeric(18, 2))
    currency = Column(String(10), default="AED")

    insurer = Column(String(255))
    insurer_contact = Column(String(100))
    insurance_type = Column(String(100))  # Fire, All Risk, etc.

    policy_path = Column(String(500))
    notes = Column(Text)

    # Relationship
    property = relationship("Property", back_populates="insurances")

    def __repr__(self):
        return f"<PropertyInsurance {self.policy_no}>"
