from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FacilityBase(BaseModel):
    """Base schema for facility data"""
    facility_no: str = Field(..., min_length=1, max_length=50)
    customer_id: str = Field(..., min_length=2, max_length=20)  # Reference to customer ID
    facility_type: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0)
    status: str = Field(default="ACTIVE", min_length=1, max_length=20)


class FacilityCreate(FacilityBase):
    """Schema for creating a new facility"""
    
    class Config:
        extra = 'forbid'


class FacilityUpdate(BaseModel):
    """Schema for updating facility data"""
    facility_no: Optional[str] = Field(None, min_length=1, max_length=50)
    facility_type: Optional[str] = Field(None, min_length=1, max_length=50)
    amount: Optional[float] = Field(None, gt=0)
    status: Optional[str] = Field(None, min_length=1, max_length=20)
    
    class Config:
        extra = 'forbid'


class FacilityResponse(FacilityBase):
    """Schema for facility response"""
    id: str  # Facility ID with 'F' prefix
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True