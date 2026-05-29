from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from app.models.facility import FacilityType, FacilityStatus
from app.schemas.validators import (
    SafeText,
    OptionalSafeText,
    Currency,
    OptionalCurrency,
    TenorMonths,
)

# Upper bound for monetary amounts (fits the NUMERIC(15, 2) DB columns).
MAX_AMOUNT = Decimal("9999999999999.99")


class FacilityBase(BaseModel):
    """Base schema for facility data"""
    customer_id: SafeText = Field(..., min_length=1, max_length=50, description="Customer ID")
    facility_type: FacilityType = Field(default=FacilityType.LOAN, description="Facility type")
    name: OptionalSafeText = Field(None, max_length=200, description="Facility name")
    status: FacilityStatus = Field(default=FacilityStatus.ACTIVE, description="Facility status")
    amount: Decimal = Field(..., gt=0, le=MAX_AMOUNT, description="Facility amount")
    outstanding: Optional[Decimal] = Field(default=0, ge=0, le=MAX_AMOUNT, description="Outstanding amount")
    currency: Currency = Field(default="AED", min_length=3, max_length=3, description="Currency (3-letter ISO code)")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date (expiry)")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Interest rate")
    tenor_months: TenorMonths = Field(None, max_length=4, description="Tenor in months")
    notes: OptionalSafeText = Field(None, max_length=1000, description="Notes")


class FacilityCreate(FacilityBase):
    """Schema for creating a new facility"""
    pass


class FacilityUpdate(BaseModel):
    """Schema for updating an existing facility"""
    customer_id: OptionalSafeText = Field(None, min_length=1, max_length=50, description="Customer ID")
    facility_type: Optional[FacilityType] = Field(None, description="Facility type")
    name: OptionalSafeText = Field(None, max_length=200, description="Facility name")
    status: Optional[FacilityStatus] = Field(None, description="Facility status")
    amount: Optional[Decimal] = Field(None, gt=0, le=MAX_AMOUNT, description="Facility amount")
    outstanding: Optional[Decimal] = Field(None, ge=0, le=MAX_AMOUNT, description="Outstanding amount")
    currency: OptionalCurrency = Field(None, min_length=3, max_length=3, description="Currency (3-letter ISO code)")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date (expiry)")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Interest rate")
    tenor_months: TenorMonths = Field(None, max_length=4, description="Tenor in months")
    notes: OptionalSafeText = Field(None, max_length=1000, description="Notes")


class FacilityResponse(FacilityBase):
    """Schema for facility API response"""
    id: str = Field(..., description="Facility ID")
    is_deleted: bool = Field(False, description="Soft delete flag")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)