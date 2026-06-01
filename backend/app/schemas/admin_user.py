"""Schemas for admin user management (match the real User model)."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime


def _validate_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    if not any(c.isalpha() for c in v):
        raise ValueError("Password must contain at least one letter")
    return v


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)
    is_admin: bool = False
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def _pw(cls, v: str) -> str:
        return _validate_password(v)


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, description="pending | viewer | editor | admin")

    @field_validator("role")
    @classmethod
    def _role(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in ("pending", "viewer", "editor", "admin"):
            raise ValueError("role must be one of: pending, viewer, editor, admin")
        return v

    @field_validator("password")
    @classmethod
    def _pw(cls, v: Optional[str]) -> Optional[str]:
        return _validate_password(v) if v is not None else v


class AdminUserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    role: str = "pending"
    auth_provider: str = "local"
    picture: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    items: List[AdminUserResponse]
    total: int
    page: int
    page_size: int
