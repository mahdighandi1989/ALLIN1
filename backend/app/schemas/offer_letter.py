from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal

from app.models.offer_letter import OfferStatus, CollateralType, RepaymentType
from app.schemas.validators import SafeText, OptionalSafeText, Currency, OptionalCurrency

MAX_AMOUNT = Decimal("9999999999999999.99")


class OfferLetterBase(BaseModel):
    customer_id: SafeText = Field(..., min_length=1, max_length=50, description="Customer ID")
    facility_id: OptionalSafeText = Field(None, max_length=50, description="Linked facility ID")
    offer_date: Optional[date] = Field(None, description="Offer date (defaults to today)")
    expiry_date: date = Field(..., description="Offer expiry date")
    status: OfferStatus = Field(default=OfferStatus.DRAFT)

    principal_amount: Decimal = Field(..., gt=0, le=MAX_AMOUNT, description="Principal")
    currency: Currency = Field(default="AED", min_length=3, max_length=3)
    interest_rate: Decimal = Field(..., ge=0, le=100, description="Annual interest rate %")
    tenor_months: int = Field(..., ge=1, le=600, description="Tenor in months")
    grace_period_months: int = Field(default=0, ge=0, le=120)
    repayment_type: RepaymentType = Field(default=RepaymentType.MONTHLY)

    processing_fee: Optional[Decimal] = Field(default=0, ge=0, le=MAX_AMOUNT)
    arrangement_fee: Optional[Decimal] = Field(default=0, ge=0, le=MAX_AMOUNT)

    collateral_type: Optional[CollateralType] = Field(None)
    collateral_value: Optional[Decimal] = Field(None, ge=0, le=MAX_AMOUNT)
    collateral_description: OptionalSafeText = Field(None, max_length=1000)
    guarantee_required: bool = Field(default=False)
    guarantee_amount: Optional[Decimal] = Field(None, ge=0, le=MAX_AMOUNT)

    purpose_of_facility: OptionalSafeText = Field(None, max_length=500)
    special_conditions: OptionalSafeText = Field(None, max_length=2000)
    covenants: OptionalSafeText = Field(None, max_length=2000)


class OfferLetterCreate(OfferLetterBase):
    pass


class OfferLetterUpdate(BaseModel):
    facility_id: OptionalSafeText = Field(None, max_length=50)
    offer_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[OfferStatus] = None
    principal_amount: Optional[Decimal] = Field(None, gt=0, le=MAX_AMOUNT)
    currency: OptionalCurrency = Field(None, min_length=3, max_length=3)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tenor_months: Optional[int] = Field(None, ge=1, le=600)
    grace_period_months: Optional[int] = Field(None, ge=0, le=120)
    repayment_type: Optional[RepaymentType] = None
    processing_fee: Optional[Decimal] = Field(None, ge=0, le=MAX_AMOUNT)
    arrangement_fee: Optional[Decimal] = Field(None, ge=0, le=MAX_AMOUNT)
    collateral_type: Optional[CollateralType] = None
    collateral_value: Optional[Decimal] = Field(None, ge=0, le=MAX_AMOUNT)
    collateral_description: OptionalSafeText = Field(None, max_length=1000)
    guarantee_required: Optional[bool] = None
    guarantee_amount: Optional[Decimal] = Field(None, ge=0, le=MAX_AMOUNT)
    purpose_of_facility: OptionalSafeText = Field(None, max_length=500)
    special_conditions: OptionalSafeText = Field(None, max_length=2000)
    covenants: OptionalSafeText = Field(None, max_length=2000)


class OfferCalculationResponse(BaseModel):
    installment_number: int
    payment_date: Optional[date] = None
    opening_balance: float
    principal_payment: float
    interest_payment: float
    total_payment: float
    closing_balance: float

    model_config = ConfigDict(from_attributes=True)


class OfferLetterResponse(BaseModel):
    id: str
    customer_id: str
    facility_id: Optional[str] = None
    offer_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None
    principal_amount: float
    currency: str = "AED"
    interest_rate: float
    tenor_months: int
    grace_period_months: Optional[int] = 0
    repayment_type: Optional[str] = None
    monthly_installment: Optional[float] = None
    total_repayment_amount: Optional[float] = None
    processing_fee: Optional[float] = None
    arrangement_fee: Optional[float] = None
    collateral_type: Optional[str] = None
    collateral_value: Optional[float] = None
    guarantee_required: Optional[bool] = False
    purpose_of_facility: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OfferLetterDetailResponse(OfferLetterResponse):
    """Offer letter plus its computed amortisation schedule."""
    customer_name: Optional[str] = None
    schedule: List[OfferCalculationResponse] = []


class OfferLetterListResponse(BaseModel):
    items: List[OfferLetterResponse]
    total: int
    page: int
    page_size: int
