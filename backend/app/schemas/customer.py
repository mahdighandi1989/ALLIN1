from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CustomerBase(BaseModel):
    """Base schema for customer data"""
    account_no: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    # Additional fields will be added gradually as per the 290+ fields requirement


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    
    class Config:
        extra = 'forbid'


class CustomerUpdate(BaseModel):
    """Schema for updating customer data"""
    account_no: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    # Additional fields will be added gradually
    
    class Config:
        extra = 'forbid'


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: str  # Customer ID with 'C' prefix
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True