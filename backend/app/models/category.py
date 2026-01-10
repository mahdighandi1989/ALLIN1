"""
Category Model
مدل دسته‌بندی‌ها - قابل توسعه
"""
from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid


class Category(Base, TimestampMixin, SoftDeleteMixin):
    """
    دسته‌بندی‌های قابل توسعه
    مثال: Retail, Corporate, VIP, SME, Individual
    با قابلیت زیرگروه‌بندی
    """
    __tablename__ = "categories"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    name_fa = Column(String(100))
    code = Column(String(20), unique=True, index=True)
    category_type = Column(String(50), default="general")  # customer, document, facility, etc.
    parent_id = Column(String(50), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Self-referential relationship for subcategories
    parent = relationship("Category", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<Category {self.name}>"
