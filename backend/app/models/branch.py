"""
Branch Model
مدل شعبات بانک
"""
from sqlalchemy import Column, String, Boolean
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid


class Branch(Base, TimestampMixin, SoftDeleteMixin):
    """شعبات بانک"""
    __tablename__ = "branches"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    branch_code = Column(String(10), unique=True, nullable=False, index=True)
    branch_name = Column(String(100))
    branch_name_fa = Column(String(100))
    city = Column(String(100))
    country = Column(String(50), default="UAE")
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Branch {self.branch_code}: {self.branch_name}>"
