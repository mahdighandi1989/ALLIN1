from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime


class TotalExposureResponse(BaseModel):
    amount: float
    currency: str


class RecentCustomerResponse(BaseModel):
    id: str
    account_no: Optional[str] = None
    name: str
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v):
        if v is None:
            return ''
        return v


class RecentActivityResponse(BaseModel):
    """A lightweight activity-feed entry derived from recent records."""
    id: int
    action: str
    timestamp: Optional[datetime] = None
    user: str = "system"


class DashboardStatsResponse(BaseModel):
    """Unified dashboard contract shared by the backend and the frontend.

    The field set is intentionally flat so it maps 1:1 onto the frontend
    ``DashboardStats`` interface and onto the documented API contract. Several
    ``expiring_*`` aliases are exposed for backward/forward compatibility.
    """
    total_customers: int
    active_customers: int
    total_facilities: int
    active_facilities: int
    expiring_soon: int
    expiring_facilities: int
    expiring_soon_facilities: int
    monthly_revenue: float
    total_outstanding: float
    total_exposure: TotalExposureResponse
    recent_customers: List[RecentCustomerResponse]
    recent_activities: List[RecentActivityResponse]

    model_config = ConfigDict(from_attributes=True)
