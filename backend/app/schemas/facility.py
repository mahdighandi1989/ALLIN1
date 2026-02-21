from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from app.models.facility import FacilityType, FacilityStatus


class FacilityBase(BaseModel):
    """Base schema for facility data"""
    customer_id: str = Field(..., description="Customer ID")
    facility_type: FacilityType = Field(default=FacilityType.LOAN, description="Facility type")
    name: Optional[str] = Field(None, max_length=200, description="Facility name")
    status: FacilityStatus = Field(default=FacilityStatus.ACTIVE, description="Facility status")
    amount: Decimal = Field(..., ge=0, description="Facility amount")
    outstanding: Optional[Decimal] = Field(default=0, ge=0, description="Outstanding amount")
    currency: str = Field(default="AED", max_length=10, description="Currency")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date (expiry)")
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Interest rate")
    tenor_months: Optional[str] = Field(None, max_length=20, description="Tenor in months")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes")


class FacilityCreate(FacilityBase):
    """Schema for creating a new facility"""
    pass


class FacilityUpdate(BaseModel):
    """Schema for updating an existing facility"""
    customer_id: Optional[str] = Field(None, description="Customer ID")
    facility_type: Optional[FacilityType] = Field(None, description="Facility type")
    name: Optional[str] = Field(None, max_length=200, description="Facility name")
    status: Optional[FacilityStatus] = Field(None, description="Facility status")
    amount: Optional[Decimal] = Field(None, ge=0, description="Facility amount")
    outstanding: Optional[Decimal] = Field(None, ge=0, description="Outstanding amount")
    currency: Optional[str] = Field(None, max_length=10, description="Currency")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date (expiry)")
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Interest rate")
    tenor_months: Optional[str] = Field(None, max_length=20, description="Tenor in months")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes")


class FacilityResponse(FacilityBase):
    """Schema for facility API response"""
    id: str = Field(..., description="Facility ID")
    is_deleted: bool = Field(False, description="Soft delete flag")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)