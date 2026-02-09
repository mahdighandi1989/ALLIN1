from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class CustomerStats(BaseModel):
    total: int
    active: int

class FacilityStats(BaseModel):
    total: int
    expiring_soon: int
    total_amount: float
    outstanding: float

class RecentCustomer(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    status: str

class RecentFacility(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    type: str
    amount: float
    status: str
    issue_date: str
    expiry_date: str

class DashboardStats(BaseModel):
    customers: CustomerStats
    facilities: FacilityStats
    recent_customers: List[RecentCustomer]
    recent_facilities: List[RecentFacility]
    
    class Config:
        from_attributes = True