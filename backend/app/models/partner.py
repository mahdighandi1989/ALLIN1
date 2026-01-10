"""
Partner Model
مدل شرکا و سهامداران
"""
from sqlalchemy import Column, String, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_short_id


class Partner(Base, TimestampMixin, SoftDeleteMixin):
    """
    شرکا و سهامداران مشتریان شرکتی
    """
    __tablename__ = "partners"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("PTR-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    partner_name = Column(String(255), nullable=False)
    nationality = Column(String(100))
    share_percent = Column(Numeric(5, 2))  # 0.00 to 100.00
    order_no = Column(Integer, default=1)

    # Additional info
    emirates_id = Column(String(50))
    passport_no = Column(String(50))
    phone = Column(String(50))
    email = Column(String(255))

    # Relationship
    customer = relationship("Customer", back_populates="partners")

    def __repr__(self):
        return f"<Partner {self.partner_name} ({self.share_percent}%)>"
