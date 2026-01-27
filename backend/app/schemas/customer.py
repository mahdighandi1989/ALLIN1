from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    national_id: str
    phone_number: str
    address: Optional[str] = None
    birth_date: Optional[datetime] = None
    email: Optional[str] = None
    customer_type: str = "individual"
    status: str = "active"

class CustomerCreate(CustomerBase):
    
    @validator('national_id')
    def validate_national_id(cls, v):
        # بررسی کد ملی ایرانی (10 رقم)
        if not re.match(r'^\d{10}$', v):
            raise ValueError('کد ملی باید 10 رقم باشد')
        
        # الگوریتم اعتبارسنجی کد ملی ایرانی
        check_digit = int(v[9])
        sum_digits = sum(int(v[i]) * (10 - i) for i in range(9))
        remainder = sum_digits % 11
        
        if remainder < 2:
            expected_check = remainder
        else:
            expected_check = 11 - remainder
            
        if check_digit != expected_check:
            raise ValueError('کد ملی معتبر نیست')
        
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # بررسی شماره تلفن ایرانی
        if not re.match(r'^(\+98|0)?9\d{9}$', v):
            raise ValueError('شماره تلفن معتبر نیست')
        return v
    
    @validator('customer_type')
    def validate_customer_type(cls, v):
        if v not in ['individual', 'corporate']:
            raise ValueError('نوع مشتری باید individual یا corporate باشد')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['active', 'inactive', 'suspended']:
            raise ValueError('وضعیت باید active، inactive یا suspended باشد')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None and v != "":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('ایمیل معتبر نیست')
        return v

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    national_id: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[datetime] = None
    email: Optional[str] = None
    customer_type: Optional[str] = None
    status: Optional[str] = None
    
    @validator('national_id')
    def validate_national_id(cls, v):
        if v is not None:
            if not re.match(r'^\d{10}$', v):
                raise ValueError('کد ملی باید 10 رقم باشد')
            
            check_digit = int(v[9])
            sum_digits = sum(int(v[i]) * (10 - i) for i in range(9))
            remainder = sum_digits % 11
            
            if remainder < 2:
                expected_check = remainder
            else:
                expected_check = 11 - remainder
                
            if check_digit != expected_check:
                raise ValueError('کد ملی معتبر نیست')
        
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None and not re.match(r'^(\+98|0)?9\d{9}$', v):
            raise ValueError('شماره تلفن معتبر نیست')
        return v
    
    @validator('customer_type')
    def validate_customer_type(cls, v):
        if v is not None and v not in ['individual', 'corporate']:
            raise ValueError('نوع مشتری باید individual یا corporate باشد')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'inactive', 'suspended']:
            raise ValueError('وضعیت باید active، inactive یا suspended باشد')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None and v != "":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('ایمیل معتبر نیست')
        return v

class CustomerResponse(CustomerBase):
    id: int
    customer_code: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True