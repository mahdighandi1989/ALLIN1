from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import List, Optional
from app.models.customer import AccountType, CustomerStatus
from app.schemas.validators import SafeText, OptionalSafeText, Phone, AccountNo


class CustomerBase(BaseModel):
    # account_no must be *present* on create (the DB column is NOT NULL), so a
    # missing key yields HTTP 422 rather than a database error. An empty string
    # is still tolerated for backward compatibility with existing clients.
    account_no: AccountNo = Field(..., max_length=50, description="Account number")
    name: SafeText = Field(..., min_length=1, max_length=200, description="Customer name")
    name_ar: OptionalSafeText = Field(None, max_length=200, description="Arabic name")
    account_type: AccountType = Field(default=AccountType.RETAIL, description="Account type")
    email: Optional[EmailStr] = Field(None, max_length=254, description="Email address")
    phone: Phone = Field(None, max_length=20, description="Phone number")
    mobile: Phone = Field(None, max_length=20, description="Mobile number")
    address: OptionalSafeText = Field(None, max_length=500, description="Address")
    branch: OptionalSafeText = Field(None, max_length=100, description="Branch")
    relationship_manager: OptionalSafeText = Field(
        None, max_length=100, description="Relationship manager"
    )
    notes: OptionalSafeText = Field(None, max_length=1000, description="Notes")
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="Customer status")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    account_no: AccountNo = Field(None, max_length=50, description="Account number")
    name: OptionalSafeText = Field(None, min_length=1, max_length=200, description="Customer name")
    name_ar: OptionalSafeText = Field(None, max_length=200)
    account_type: Optional[AccountType] = Field(None, description="Account type")
    email: Optional[EmailStr] = Field(None, max_length=254, description="Email address")
    phone: Phone = Field(None, max_length=20, description="Phone number")
    mobile: Phone = Field(None, max_length=20)
    address: OptionalSafeText = Field(None, max_length=500)
    branch: OptionalSafeText = Field(None, max_length=100)
    relationship_manager: OptionalSafeText = Field(None, max_length=100)
    notes: OptionalSafeText = Field(None, max_length=1000)
    status: Optional[CustomerStatus] = Field(None, description="Customer status")


class CustomerResponse(CustomerBase):
    id: str = Field(..., description="Customer ID")
    is_deleted: bool = Field(False, description="Soft delete flag")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    """Paginated envelope for customer list responses."""
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
