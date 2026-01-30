from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class CustomerBase(BaseModel):
    """Base schema for customer data"""
    account_no: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    name_ar: Optional[str] = Field(None, max_length=200)
    account_type: str = Field(default="retail", regex="^(retail|corporate|sme)$")
    email: Optional[str] = Field(None, max_length=100, regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    branch: Optional[str] = Field(None, max_length=100)
    relationship_manager: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('account_no')
    def validate_account_no(cls, v):
        if not v or not v.strip():
            raise ValueError('Account number cannot be empty')
        # Remove whitespace and validate format
        v = v.strip()
        if not re.match(r'^[A-Z0-9][A-Z0-9\-_]{0,49}$', v.upper()):
            raise ValueError('Account number must contain only letters, numbers, hyphens and underscores')
        return v.upper()

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Customer name cannot be empty')
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Customer name must be at least 2 characters')
        # Allow letters, spaces, dots, apostrophes, hyphens
        if not re.match(r"^[a-zA-Z\s\.\'\-]+$", v):
            raise ValueError('Customer name contains invalid characters')
        return v

    @validator('name_ar')
    def validate_name_ar(cls, v):
        if v is not None:
            v = v.strip()
            if v == '':
                return None
            if len(v) < 2:
                raise ValueError('Arabic name must be at least 2 characters')
        return v

    @validator('phone', 'mobile')
    def validate_phone_numbers(cls, v):
        if v is not None:
            v = v.strip()
            if v == '':
                return None
            # Remove common separators and validate
            clean_phone = re.sub(r'[\s\-\(\)\+]', '', v)
            if not re.match(r'^\d{7,15}$', clean_phone):
                raise ValueError('Phone number must contain 7-15 digits')
        return v


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    
    class Config:
        extra = 'forbid'
        str_strip_whitespace = True


class CustomerUpdate(BaseModel):
    """Schema for updating customer data"""
    account_no: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_ar: Optional[str] = Field(None, max_length=200)
    account_type: Optional[str] = Field(None, regex="^(retail|corporate|sme)$")
    email: Optional[str] = Field(None, max_length=100, regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    branch: Optional[str] = Field(None, max_length=100)
    relationship_manager: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('account_no')
    def validate_account_no(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Account number cannot be empty')
            v = v.strip()
            if not re.match(r'^[A-Z0-9][A-Z0-9\-_]{0,49}$', v.upper()):
                raise ValueError('Account number must contain only letters, numbers, hyphens and underscores')
            return v.upper()
        return v

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Customer name cannot be empty')
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Customer name must be at least 2 characters')
            if not re.match(r"^[a-zA-Z\s\.\'\-]+$", v):
                raise ValueError('Customer name contains invalid characters')
        return v

    @validator('name_ar')
    def validate_name_ar(cls, v):
        if v is not None:
            v = v.strip()
            if v == '':
                return None
            if len(v) < 2:
                raise ValueError('Arabic name must be at least 2 characters')
        return v

    @validator('phone', 'mobile')
    def validate_phone_numbers(cls, v):
        if v is not None:
            v = v.strip()
            if v == '':
                return None
            clean_phone = re.sub(r'[\s\-\(\)\+]', '', v)
            if not re.match(r'^\d{7,15}$', clean_phone):
                raise ValueError('Phone number must contain 7-15 digits')
        return v
    
    class Config:
        extra = 'forbid'
        str_strip_whitespace = True


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: str = Field(..., min_length=33, max_length=33, regex=r'^C[A-F0-9]{32}$')
    status: str = Field(..., regex="^(active|inactive|suspended)$")
    created_at: datetime
    updated_at: Optional[datetime] = None

    @validator('id')
    def validate_customer_id(cls, v):
        if not v:
            raise ValueError('Customer ID is required')
        if not isinstance(v, str):
            raise ValueError('Customer ID must be a string')
        if len(v) != 33:
            raise ValueError('Customer ID must be exactly 33 characters long')
        if not v.startswith('C'):
            raise ValueError('Customer ID must start with "C"')
        if not re.match(r'^C[A-F0-9]{32}$', v):
            raise ValueError('Customer ID format is invalid (must be C followed by 32 hexadecimal characters)')
        return v
    
    class Config:
        orm_mode = True
        str_strip_whitespace = True


class CustomerListResponse(BaseModel):
    """Schema for paginated customer list response"""
    items: list[CustomerResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=1000)
    pages: int = Field(..., ge=0)

    @validator('pages')
    def validate_pages(cls, v, values):
        if 'total' in values and 'page_size' in values:
            expected_pages = (values['total'] + values['page_size'] - 1) // values['page_size'] if values['page_size'] > 0 else 0
            if v != expected_pages:
                raise ValueError('Pages calculation is incorrect')
        return v

    class Config:
        extra = 'forbid'


class CustomerSummaryResponse(BaseModel):
    """Schema for customer summary statistics"""
    total: int = Field(..., ge=0)
    active: int = Field(..., ge=0)
    inactive: int = Field(..., ge=0)
    suspended: int = Field(..., ge=0)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    recent_count: int = Field(..., ge=0)

    @validator('by_type')
    def validate_by_type(cls, v):
        allowed_types = {'retail', 'corporate', 'sme'}
        for key in v.keys():
            if key not in allowed_types:
                raise ValueError(f'Invalid account type: {key}')
            if not isinstance(v[key], int) or v[key] < 0:
                raise ValueError(f'Count for {key} must be a non-negative integer')
        return v

    @validator('by_status')
    def validate_by_status(cls, v):
        allowed_statuses = {'active', 'inactive', 'suspended'}
        for key in v.keys():
            if key not in allowed_statuses:
                raise ValueError(f'Invalid status: {key}')
            if not isinstance(v[key], int) or v[key] < 0:
                raise ValueError(f'Count for {key} must be a non-negative integer')
        return v

    class Config:
        extra = 'forbid'