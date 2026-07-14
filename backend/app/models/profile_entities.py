"""Per-customer profile child entities carried over from the Excel system:
mortgaged properties, fixed deposits, and partners/shareholders.

Each is linked to a customer by ``account_no`` (the system-wide key), mirroring
``app.models.guarantor.Guarantor`` so a customer's profile can list and edit
them. They capture the structured fields the legacy ``PF_*`` profile recorded
(and the user's requirement A12 in the «پرامپت» sheet), which until now survived
only as free text (FD), a ``data_json`` blob (partners), or a static frontend
array (properties).
"""
from sqlalchemy import Column, String, Numeric, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class MortgagedProperty(Base):
    """A mortgaged property pledged as collateral (PROPERTIES-UAE / -IRAN)."""

    __tablename__ = "mortgaged_properties"

    id = Column(String(60), primary_key=True)
    account_no = Column(String(50), index=True, nullable=False)
    # Optional link to the specific facility this property collateralises. Empty
    # means it secures the customer generally (the legacy behaviour); when set it
    # lets the property surface under that facility, not just under the customer.
    facility_id = Column(String(60), index=True)
    customer_name = Column(String(200))
    country = Column(String(20))             # UAE / Iran
    plate_no = Column(String(80))            # شماره پلاک ثبتی
    mortgage_deed_no = Column(String(80))    # شماره سند رهنی
    city = Column(String(80))                # شهر
    address = Column(String(400))            # نشانی ملک
    prop_type = Column(String(80))           # نوع
    building_age = Column(String(40))        # عمر/سن ساختمان
    land_area = Column(String(40))           # مساحت زمین (م۲)
    cnbc = Column(String(80))                # بررسی زیرساخت (CNBC)
    zone = Column(String(40))                # منطقه
    infra_area = Column(String(40))          # مساحت زیربنا (م²)
    owner = Column(String(200))              # مالک / راهن
    owner_national_id = Column(String(40))   # کد ملی مالک/راهن
    postal_code = Column(String(20))         # کد پستی ملک
    valuation = Column(Numeric(18, 2))       # ارزیابی / برآورد
    valuation_currency = Column(String(10), default="AED")
    insurance_expiry = Column(String(30))    # تاریخ انقضای بیمه‌نامه
    insurance_issue = Column(String(30))     # تاریخ صدور بیمه‌نامه
    insurance_no = Column(String(80))        # شماره بیمه‌نامه
    insurance_computer_code = Column(String(80))  # کد رایانهٔ بیمه
    last_valuation_date = Column(String(30)) # تاریخ آخرین ارزیابی
    mortgage_date = Column(String(30))       # تاریخ ترهین
    mortgage_amount = Column(Numeric(18, 2)) # مبلغ ترهین
    mortgage_currency = Column(String(10), default="AED")  # ارز مبلغ ترهین
    remarks = Column(String(400))
    created_by = Column(String(80))
    date_added = Column(String(30))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)


class FixedDeposit(Base):
    """A fixed deposit held as security (PF_FD1..FD5 in the Excel profile)."""

    __tablename__ = "fixed_deposits"

    id = Column(String(60), primary_key=True)
    account_no = Column(String(50), index=True, nullable=False)
    # Optional link to the specific facility this deposit secures.
    facility_id = Column(String(60), index=True)
    customer_name = Column(String(200))
    fd_number = Column(String(80))
    amount = Column(Numeric(18, 2))
    currency = Column(String(10), default="AED")
    open_date = Column(String(30))
    maturity_date = Column(String(30))
    rate = Column(String(40))                # kept as text ('4.5%', '4.5')
    remarks = Column(String(400))
    created_by = Column(String(80))
    date_added = Column(String(30))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)


class Partner(Base):
    """A partner / shareholder of a corporate customer (PF_Partner1..8)."""

    __tablename__ = "partners"

    id = Column(String(60), primary_key=True)
    account_no = Column(String(50), index=True, nullable=False)
    # Optional link to the specific facility this partner/shareholder relates to.
    facility_id = Column(String(60), index=True)
    customer_name = Column(String(200))
    name = Column(String(200))
    role = Column(String(80))                # سمت: Partner / Manager / Director / Authorized Signatory …
    nationality = Column(String(80))
    national_id = Column(String(40))         # کد ملی
    passport_no = Column(String(80))
    passport_issue = Column(String(30))
    passport_expiry = Column(String(30))
    emirates_id_no = Column(String(80))
    emirates_id_expiry = Column(String(30))
    share = Column(String(40))               # share % (text: '25', '25%')
    remarks = Column(String(400))
    created_by = Column(String(80))
    date_added = Column(String(30))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)
