from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.customer import AccountType, CustomerStatus


class CustomerBase(BaseModel):
    """Base schema for customer data"""
    account_no: str = Field(..., min_length=1, max_length=50, description="Customer account number")
    name: str = Field(..., min_length=1, max_length=200, description="Customer name")
    name_ar: Optional[str] = Field(None, max_length=200, description="Customer name in Arabic")
    account_type: AccountType = Field(default=AccountType.RETAIL, description="Account type")
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="Customer status")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    mobile: Optional[str] = Field(None, max_length=50, description="Mobile number")
    address: Optional[str] = Field(None, description="Customer address")
    branch: Optional[str] = Field(None, max_length=100, description="Branch name")
    relationship_manager: Optional[str] = Field(None, max_length=100, description="Relationship manager")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
        validate_assignment=True
    )


class CustomerUpdate(BaseModel):
    """Schema for updating customer data"""
    account_no: Optional[str] = Field(None, min_length=1, max_length=50, description="Customer account number")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Customer name")
    name_ar: Optional[str] = Field(None, max_length=200, description="Customer name in Arabic")
    account_type: Optional[AccountType] = Field(None, description="Account type")
    status: Optional[CustomerStatus] = Field(None, description="Customer status")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    mobile: Optional[str] = Field(None, max_length=50, description="Mobile number")
    address: Optional[str] = Field(None, description="Customer address")
    branch: Optional[str] = Field(None, max_length=100, description="Branch name")
    relationship_manager: Optional[str] = Field(None, max_length=100, description="Relationship manager")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
        validate_assignment=True
    )


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: str = Field(..., description="Customer ID with 'C' prefix")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )


class CustomerSummary(BaseModel):
    """Schema for customer summary statistics"""
    total: int = Field(..., description="Total number of customers")
    active: int = Field(..., description="Number of active customers")
    inactive: int = Field(..., description="Number of inactive customers")
    suspended: int = Field(..., description="Number of suspended customers")
    by_type: dict[str, int] = Field(..., description="Count by account type")
    by_status: dict[str, int] = Field(..., description="Count by status")
    recent_count: int = Field(..., description="Recent customers (last 30 days)")
    
    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    """Schema for paginated customer list response"""
    items: list[CustomerResponse] = Field(..., description="List of customers")
    total: int = Field(..., description="Total number of customers")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(from_attributes=True)