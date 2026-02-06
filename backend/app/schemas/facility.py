from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class FacilityType(str, Enum):
    """Facility type enumeration"""
    LOAN = "loan"
    OVERDRAFT = "overdraft"
    LC = "lc"
    LG = "lg"
    OTHER = "other"


class FacilityStatus(str, Enum):
    """Facility status enumeration"""
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"
    DEFAULTED = "defaulted"


class FacilityBase(BaseModel):
    """Base schema for facility data"""
    customer_id: str = Field(..., min_length=1, max_length=50, description="Customer ID")
    facility_type: FacilityType = Field(..., description="Type of facility")
    name: Optional[str] = Field(None, max_length=200, description="Facility name")
    amount: Decimal = Field(..., gt=0, description="Facility amount")
    currency: str = Field(default="AED", min_length=3, max_length=10, description="Currency code")
    outstanding: Optional[Decimal] = Field(None, ge=0, description="Outstanding amount")
    start_date: Optional[date] = Field(None, description="Facility start date")
    expiry_date: Optional[date] = Field(None, description="Facility expiry date")
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Interest rate percentage")
    tenor_months: Optional[str] = Field(None, max_length=20, description="Tenor in months")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class FacilityCreate(FacilityBase):
    """Schema for creating a new facility"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )


class FacilityUpdate(BaseModel):
    """Schema for updating facility data"""
    facility_type: Optional[FacilityType] = Field(None, description="Type of facility")
    name: Optional[str] = Field(None, max_length=200, description="Facility name")
    amount: Optional[Decimal] = Field(None, gt=0, description="Facility amount")
    currency: Optional[str] = Field(None, min_length=3, max_length=10, description="Currency code")
    outstanding: Optional[Decimal] = Field(None, ge=0, description="Outstanding amount")
    start_date: Optional[date] = Field(None, description="Facility start date")
    expiry_date: Optional[date] = Field(None, description="Facility expiry date")
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Interest rate percentage")
    tenor_months: Optional[str] = Field(None, max_length=20, description="Tenor in months")
    status: Optional[FacilityStatus] = Field(None, description="Facility status")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )


class FacilityResponse(FacilityBase):
    """Schema for facility response"""
    id: str = Field(..., description="Facility ID with 'F' prefix")
    status: FacilityStatus = Field(..., description="Facility status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Optional customer information for joined queries
    customer_name: Optional[str] = Field(None, description="Customer name")
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class FacilityListResponse(BaseModel):
    """Schema for paginated facility list response"""
    items: list[FacilityResponse] = Field(..., description="List of facilities")
    total: int = Field(..., ge=0, description="Total number of facilities")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")
    
    model_config = ConfigDict(
        from_attributes=True
    )


class FacilitySearchParams(BaseModel):
    """Schema for facility search parameters"""
    customer_id: Optional[str] = Field(None, min_length=1, max_length=50, description="Filter by customer ID")
    facility_type: Optional[FacilityType] = Field(None, description="Filter by facility type")
    status: Optional[FacilityStatus] = Field(None, description="Filter by status")
    search: Optional[str] = Field(None, min_length=1, max_length=200, description="Search in facility name")
    amount_from: Optional[Decimal] = Field(None, ge=0, description="Minimum amount filter")
    amount_to: Optional[Decimal] = Field(None, ge=0, description="Maximum amount filter")
    date_from: Optional[date] = Field(None, description="Start date filter")
    date_to: Optional[date] = Field(None, description="End date filter")
    expiry_from: Optional[date] = Field(None, description="Expiry date from filter")
    expiry_to: Optional[date] = Field(None, description="Expiry date to filter")
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Search by customer name")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )


class FacilityStatusUpdate(BaseModel):
    """Schema for facility status update"""
    status: FacilityStatus = Field(..., description="New facility status")
    notes: Optional[str] = Field(None, max_length=1000, description="Status change notes")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )


class FacilitySummary(BaseModel):
    """Schema for facility summary statistics"""
    total_facilities: int = Field(..., ge=0, description="Total number of facilities")
    total_amount: Decimal = Field(..., ge=0, description="Total facility amount")
    total_outstanding: Decimal = Field(..., ge=0, description="Total outstanding amount")
    by_type: dict[str, int] = Field(..., description="Facilities count by type")
    by_status: dict[str, int] = Field(..., description="Facilities count by status")
    by_currency: dict[str, Decimal] = Field(..., description="Total amounts by currency")
    expiring_soon: int = Field(..., ge=0, description="Facilities expiring in next 30 days")
    
    model_config = ConfigDict(
        from_attributes=True
    )