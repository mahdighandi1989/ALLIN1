from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime, date


class TotalExposureResponse(BaseModel):
    amount: float
    currency: str


class OtherStatsResponse(BaseModel):
    """The non-amount aggregate scalars of the dashboard, grouped in one object.

    Exposed alongside the flat ``total_amount`` so a consumer that just wants
    "the total amount plus everything else" has a single, documented place to
    read the remaining counts/totals from. Every field mirrors a top-level field
    on :class:`DashboardStatsResponse`, so this is purely additive — the
    top-level fields remain the canonical source of truth.
    """
    total_customers: int
    active_customers: int
    total_facilities: int
    active_facilities: int
    expiring_soon: int
    monthly_revenue: float
    total_outstanding: float
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


class BreakdownItem(BaseModel):
    """A single labelled slice for a chart (e.g. facility-type distribution)."""
    label: str
    count: int
    amount: float = 0.0


class MonthlyTrendItem(BaseModel):
    """One month of the exposure/revenue trend line."""
    month: str  # YYYY-MM
    exposure: float = 0.0
    facilities: int = 0


class ExpiringFacilityItem(BaseModel):
    """A facility approaching its expiry date (for the watch-list table)."""
    id: str
    name: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    facility_type: Optional[str] = None
    amount: float = 0.0
    currency: str = "AED"
    expiry_date: Optional[date] = None
    days_to_expiry: Optional[int] = None
    status: Optional[str] = None


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
    # Flat sum of every facility's ``amount`` in the base currency. This is the
    # headline "total amount" the dashboard shows; it equals
    # ``total_exposure.amount`` and is surfaced as a plain number so consumers
    # (and the documented API contract) can read it without unwrapping the
    # nested ``total_exposure`` object.
    total_amount: float
    # The remaining aggregate scalars grouped together (see OtherStatsResponse).
    other_stats: OtherStatsResponse
    recent_customers: List[RecentCustomerResponse]
    recent_activities: List[RecentActivityResponse]

    # Richer analytics for the dashboard charts/tables.
    facility_type_breakdown: List[BreakdownItem] = []
    facility_status_breakdown: List[BreakdownItem] = []
    risk_rating_breakdown: List[BreakdownItem] = []
    customer_type_breakdown: List[BreakdownItem] = []
    monthly_trend: List[MonthlyTrendItem] = []
    expiring_facilities_list: List[ExpiringFacilityItem] = []

    model_config = ConfigDict(from_attributes=True)
