from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum
from app.models.customer import AccountType, CustomerStatus
from app.schemas.validators import SafeText, OptionalSafeText, Phone, AccountNo


class CustomerBase(BaseModel):
    account_no: AccountNo = Field(None, max_length=50, description="Account number")
    name: SafeText = Field(..., min_length=1, max_length=200, description="Customer name")
    account_type: AccountType = Field(default=AccountType.RETAIL, description="Account type")
    email: Optional[EmailStr] = Field(None, max_length=254, description="Email address")
    phone: Phone = Field(None, max_length=20, description="Phone number")
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="Customer status")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    account_no: AccountNo = Field(None, max_length=50, description="Account number")
    name: OptionalSafeText = Field(None, min_length=1, max_length=200, description="Customer name")
    account_type: Optional[AccountType] = Field(None, description="Account type")
    email: Optional[EmailStr] = Field(None, max_length=254, description="Email address")
    phone: Phone = Field(None, max_length=20, description="Phone number")
    status: Optional[CustomerStatus] = Field(None, description="Customer status")


class CustomerResponse(CustomerBase):
    id: str = Field(..., description="Customer ID")
    is_deleted: bool = Field(False, description="Soft delete flag")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)