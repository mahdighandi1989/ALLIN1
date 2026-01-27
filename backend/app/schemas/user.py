from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    is_active: bool = True
    role: str = "user"

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('رمز عبور باید حداقل 8 کاراکتر باشد')
        if not re.search(r'[A-Z]', v):
            raise ValueError('رمز عبور باید حداقل یک حرف بزرگ داشته باشد')
        if not re.search(r'[a-z]', v):
            raise ValueError('رمز عبور باید حداقل یک حرف کوچک داشته باشد')
        if not re.search(r'\d', v):
            raise ValueError('رمز عبور باید حداقل یک عدد داشته باشد')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('رمز عبور باید حداقل یک کاراکتر خاص داشته باشد')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('نام کاربری باید حداقل 3 کاراکتر باشد')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('نام کاربری فقط می‌تواند شامل حروف، اعداد و _ باشد')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'user']:
            raise ValueError('نقش کاربر باید admin یا user باشد')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('رمز عبور باید حداقل 8 کاراکتر باشد')
            if not re.search(r'[A-Z]', v):
                raise ValueError('رمز عبور باید حداقل یک حرف بزرگ داشته باشد')
            if not re.search(r'[a-z]', v):
                raise ValueError('رمز عبور باید حداقل یک حرف کوچک داشته باشد')
            if not re.search(r'\d', v):
                raise ValueError('رمز عبور باید حداقل یک عدد داشته باشد')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('رمز عبور باید حداقل یک کاراکتر خاص داشته باشد')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('نام کاربری باید حداقل 3 کاراکتر باشد')
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError('نام کاربری فقط می‌تواند شامل حروف، اعداد و _ باشد')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ['admin', 'user']:
            raise ValueError('نقش کاربر باید admin یا user باشد')
        return v

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True