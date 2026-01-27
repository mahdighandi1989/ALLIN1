from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class FacilityType(str, Enum):
    LOAN = "LOAN"
    OVERDRAFT = "OVERDRAFT"
    LC = "LC"  # Letter of Credit
    LG = "LG"  # Letter of Guarantee

class FacilityStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class LoanType(str, Enum):
    PERSONAL = "PERSONAL"
    MORTGAGE = "MORTGAGE"
    BUSINESS = "BUSINESS"
    AUTO = "AUTO"
    EDUCATION = "EDUCATION"

class Currency(str, Enum):
    IRR = "IRR"  # Iranian Rial
    USD = "USD"
    EUR = "EUR"

class InterestRateType(str, Enum):
    FIXED = "FIXED"
    VARIABLE = "VARIABLE"

class FacilityBase(BaseModel):
    customer_id: str = Field(..., min_length=1)
    facility_type: FacilityType
    loan_type: Optional[LoanType] = None
    amount: Decimal = Field(..., gt=0)
    currency: Currency = Currency.IRR
    interest_rate: float = Field(..., ge=0, le=100)
    interest_rate_type: InterestRateType = InterestRateType.FIXED
    duration_months: int = Field(..., gt=0, le=600)  # max 50 years
    purpose: str = Field(..., min_length=10, max_length=500)
    collateral_description: Optional[str] = Field(None, max_length=1000)
    collateral_value: Optional[Decimal] = Field(None, ge=0)
    guarantor_name: Optional[str] = Field(None, max_length=100)
    guarantor_national_id: Optional[str] = Field(None, min_length=10, max_length=10)
    guarantor_phone: Optional[str] = Field(None, min_length=11, max_length=11)
    monthly_payment: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('guarantor_national_id')
    def validate_guarantor_national_id(cls, v):
        if v and not v.isdigit():
            raise ValueError('شناسه ملی ضامن باید فقط شامل اعداد باشد')
        return v
    
    @validator('guarantor_phone')
    def validate_guarantor_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('شماره تلفن ضامن باید فقط شامل اعداد باشد')
        return v

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    interest_rate_type: Optional[InterestRateType] = None
    duration_months: Optional[int] = Field(None, gt=0, le=600)
    purpose: Optional[str] = Field(None, min_length=10, max_length=500)
    collateral_description: Optional[str] = Field(None, max_length=1000)
    collateral_value: Optional[Decimal] = Field(None, ge=0)
    guarantor_name: Optional[str] = Field(None, max_length=100)
    guarantor_national_id: Optional[str] = Field(None, min_length=10, max_length=10)
    guarantor_phone: Optional[str] = Field(None, min_length=11, max_length=11)
    monthly_payment: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[FacilityStatus] = None

class FacilityResponse(FacilityBase):
    id: str
    facility_id: str
    status: FacilityStatus
    remaining_balance: Optional[Decimal] = None
    next_payment_date: Optional[date] = None
    total_paid: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class FacilityListResponse(BaseModel):
    facilities: List[FacilityResponse]
    total: int
    page: int
    page_size: int

class FacilitySummary(BaseModel):
    total_facilities: int
    total_amount: Decimal
    active_facilities: int
    pending_facilities: int
    by_type: dict
    by_status: dict