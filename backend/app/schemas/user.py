from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v
    
    class Config:
        extra = 'forbid'


class UserUpdate(BaseModel):
    """Schema for updating user data"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    
    @validator('password')
    def validate_password_strength(cls, v):
        if v is not None:
            if not any(char.isdigit() for char in v):
                raise ValueError('Password must contain at least one digit')
            if not any(char.isalpha() for char in v):
                raise ValueError('Password must contain at least one letter')
        return v
    
    class Config:
        extra = 'forbid'


class UserResponse(UserBase):
    """Schema for user response (without password)"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[int] = None
    email: Optional[str] = None