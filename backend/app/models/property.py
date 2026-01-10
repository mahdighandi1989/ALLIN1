"""
Property Models
مدل‌های املاک و وثایق ملکی
"""
from datetime import date
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Integer,
    ForeignKey, Text, JSON, Numeric, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin, generate_short_id


class PropertyLocation(str, Enum):
    """موقعیت ملک"""
    UAE = "UAE"
    IRAN = "IRAN"
    OTHER = "OTHER"


class PropertyType(str, Enum):
    """نوع ملک"""
    VILLA = "Villa"
    APARTMENT = "Apartment"
    OFFICE = "Office"
    WAREHOUSE = "Warehouse"
    LAND = "Land"
    SHOP = "Shop"
    BUILDING = "Building"
    OTHER = "Other"


class PropertyStatus(str, Enum):
    """وضعیت ملک"""
    MORTGAGED = "Mortgaged"  # رهنی
    FREE = "Free"  # آزاد
    UNDER_LIEN = "Under Lien"  # در رهن
    SOLD = "Sold"  # فروخته شده


class Property(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    مدل املاک
    شامل اطلاعات کامل ملک و وضعیت وثیقه
    """
    __tablename__ = "properties"

    id = Column(String(50), primary_key=True, default=lambda: generate_short_id("PRP-"))
    customer_id = Column(String(50), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # موقعیت و نوع
    location = Column(SQLEnum(PropertyLocation), default=PropertyLocation.UAE, nullable=False)
    property_type = Column(SQLEnum(PropertyType), default=PropertyType.APARTMENT, nullable=False)
    status = Column(SQLEnum(PropertyStatus), default=PropertyStatus.FREE, nullable=False)

    # شناسه‌ها
    plate_no = Column(String(50), nullable=True)  # پلاک
    deed_no = Column(String(50), nullable=True)  # شماره سند
    makani_no = Column(String(50), nullable=True)  # شماره مکانی (امارات)
    ejari_no = Column(String(50), nullable=True)  # شماره اجاری

    # آدرس
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    area = Column(String(100), nullable=True)
    building_name = Column(String(200), nullable=True)
    unit_no = Column(String(50), nullable=True)

    # ابعاد و مشخصات
    area_sqft = Column(Numeric(12, 2), nullable=True)
    area_sqm = Column(Numeric(12, 2), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    floors = Column(Integer, nullable=True)

    # ارزش
    purchase_value = Column(Numeric(18, 2), nullable=True)
    purchase_date = Column(Date, nullable=True)
    current_value = Column(Numeric(18, 2), nullable=True)
    valuation_date = Column(Date, nullable=True)
    mortgage_value = Column(Numeric(18, 2), nullable=True)
    currency = Column(String(10), default="AED")

    # وثیقه
    lien_amount = Column(Numeric(18, 2), nullable=True)
    lien_date = Column(Date, nullable=True)
    lien_release_date = Column(Date, nullable=True)
    mortgage_bank = Column(String(200), nullable=True)
    mortgage_reference = Column(String(100), nullable=True)

    # مالکیت
    owner_name = Column(String(255), nullable=True)
    ownership_percentage = Column(Numeric(5, 2), default=100)
    co_owners = Column(JSON, default=list)  # [{name, percentage}, ...]

    # مستندات
    documents = Column(JSON, default=list)  # لیست اسناد

    # یادداشت
    notes = Column(Text, nullable=True)

    # متادیتا
    custom_fields = Column(JSON, default=dict)

    # روابط
    customer = relationship("Customer", back_populates="properties")
    valuations = relationship("PropertyValuation", back_populates="property", cascade="all, delete-orphan")
    insurances = relationship("PropertyInsurance", back_populates="property", cascade="all, delete-orphan")

    @property
    def ltv_ratio(self) -> float:
        """نسبت وام به ارزش"""
        if self.current_value and self.current_value > 0 and self.lien_amount:
            return float(self.lien_amount) / float(self.current_value) * 100
        return 0

    def __repr__(self):
        return f"<Property {self.id}: {self.property_type.value} in {self.location.value}>"
