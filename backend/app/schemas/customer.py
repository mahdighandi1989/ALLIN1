"""Customer Schemas"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime


class CustomerCreate(BaseModel):
    account_no: str
    name: str
    name_ar: Optional[str] = None
    account_type: str = "retail"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    branch: Optional[str] = None
    relationship_manager: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    account_type: Optional[str] = None
    status: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    branch: Optional[str] = None
    relationship_manager: Optional[str] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    account_no: str
    name: str
    name_ar: Optional[str]
    account_type: str
    status: str
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    address: Optional[str]
    branch: Optional[str]
    relationship_manager: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CustomerList(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
