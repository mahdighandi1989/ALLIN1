from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class CustomerType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    CORPORATE = "CORPORATE"

class CustomerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class MaritalStatus(str, Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"

class CustomerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    national_id: str = Field(..., min_length=10, max_length=10)
    birth_date: date
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=11, max_length=11)
    mobile: Optional[str] = Field(None, min_length=11, max_length=11)
    address: str = Field(..., min_length=10, max_length=500)
    postal_code: str = Field(..., min_length=10, max_length=10)
    city: str = Field(..., min_length=2, max_length=50)
    province: str = Field(..., min_length=2, max_length=50)
    customer_type: CustomerType
    marital_status: Optional[MaritalStatus] = None
    education_level: Optional[str] = Field(None, max_length=50)
    occupation: Optional[str] = Field(None, max_length=100)
    monthly_income: Optional[float] = Field(None, ge=0)
    company_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    work_experience_years: Optional[int] = Field(None, ge=0, le=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, min_length=11, max_length=11)
    risk_level: Optional[str] = Field("LOW", max_length=20)
    
    @validator('national_id')
    def validate_national_id(cls, v):
        if not v.isdigit():
            raise ValueError('شناسه ملی باید فقط شامل اعداد باشد')
        return v
    
    @validator('phone', 'mobile', 'emergency_contact_phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('شماره تلفن باید فقط شامل اعداد باشد')
        return v
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        if not v.isdigit():
            raise ValueError('کد پستی باید فقط شامل اعداد باشد')
        return v

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=11, max_length=11)
    mobile: Optional[str] = Field(None, min_length=11, max_length=11)
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    postal_code: Optional[str] = Field(None, min_length=10, max_length=10)
    city: Optional[str] = Field(None, min_length=2, max_length=50)
    province: Optional[str] = Field(None, min_length=2, max_length=50)
    marital_status: Optional[MaritalStatus] = None
    education_level: Optional[str] = Field(None, max_length=50)
    occupation: Optional[str] = Field(None, max_length=100)
    monthly_income: Optional[float] = Field(None, ge=0)
    company_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    work_experience_years: Optional[int] = Field(None, ge=0, le=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, min_length=11, max_length=11)
    risk_level: Optional[str] = Field(None, max_length=20)
    status: Optional[CustomerStatus] = None

class CustomerResponse(CustomerBase):
    id: str
    customer_id: str
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    page: int
    page_size: int