"""Facility Schemas"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


class FacilityCreate(BaseModel):
    customer_id: str
    facility_type: str
    name: Optional[str] = None
    amount: Decimal
    currency: str = "AED"
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    tenor_months: Optional[str] = None
    notes: Optional[str] = None


class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[Decimal] = None
    outstanding: Optional[Decimal] = None
    currency: Optional[str] = None
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    tenor_months: Optional[str] = None
    notes: Optional[str] = None


class FacilityResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: Optional[str] = None
    facility_type: str
    name: Optional[str]
    status: str
    amount: float
    outstanding: float
    currency: str
    start_date: Optional[date]
    expiry_date: Optional[date]
    interest_rate: Optional[float]
    tenor_months: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class FacilityList(BaseModel):
    items: List[FacilityResponse]
    total: int
    page: int
    page_size: int
