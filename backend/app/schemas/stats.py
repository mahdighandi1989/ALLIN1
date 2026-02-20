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


class DashboardStatsResponse(BaseModel):
    total_customers: int
    active_customers: int
    total_facilities: int
    expiring_soon_facilities: int
    total_exposure: TotalExposureResponse
    recent_customers: List[RecentCustomerResponse]

    model_config = ConfigDict(from_attributes=True)