from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional
from app.models.customer import AccountType, CustomerStatus
from app.schemas.validators import SafeText, OptionalSafeText, Phone, AccountNo


class _EmailNormalizerMixin:
    """Treat empty/blank email as None.

    Legacy databases (and lax clients) store ``email = ''``; a strict EmailStr
    would reject that and 500 the *response*. Normalising blank -> None keeps
    real (non-empty) emails fully validated while tolerating empty ones.
    """

    @field_validator("email", mode="before", check_fields=False)
    @classmethod
    def _blank_email_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class CustomerBase(_EmailNormalizerMixin, BaseModel):
    # account_no must be *present* on create (the DB column is NOT NULL), so a
    # missing key yields HTTP 422 rather than a database error. An empty string
    # is still tolerated for backward compatibility with existing clients.
    account_no: AccountNo = Field(..., max_length=50, description="Account number")
    name: SafeText = Field(..., min_length=1, max_length=200, description="Customer name")
    name_ar: OptionalSafeText = Field(None, max_length=200, description="Arabic name")
    account_type: AccountType = Field(default=AccountType.RETAIL, description="Account type")
    email: Optional[EmailStr] = Field(None, max_length=254, description="Email address")
    phone: Phone = Field(None, max_length=20, description="Phone number")
    mobile: Phone = Field(None, max_length=20, description="Mobile number")
    address: OptionalSafeText = Field(None, max_length=500, description="Address")
    branch: OptionalSafeText = Field(None, max_length=100, description="Branch")
    relationship_manager: OptionalSafeText = Field(
        None, max_length=100, description="Relationship manager"
    )
    notes: OptionalSafeText = Field(None, max_length=1000, description="Notes")
    status: CustomerStatus = Field(default=CustomerStatus.ACTIVE, description="Customer status")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(_EmailNormalizerMixin, BaseModel):
    account_no: AccountNo = Field(None, max_length=50, description="Account number")
    name: OptionalSafeText = Field(None, min_length=1, max_length=200, description="Customer name")
    name_ar: OptionalSafeText = Field(None, max_length=200)
    account_type: Optional[AccountType] = Field(None, description="Account type")
    email: Optional[EmailStr] = Field(None, max_length=254, description="Email address")
    phone: Phone = Field(None, max_length=20, description="Phone number")
    mobile: Phone = Field(None, max_length=20)
    address: OptionalSafeText = Field(None, max_length=500)
    branch: OptionalSafeText = Field(None, max_length=100)
    relationship_manager: OptionalSafeText = Field(None, max_length=100)
    notes: OptionalSafeText = Field(None, max_length=1000)
    status: Optional[CustomerStatus] = Field(None, description="Customer status")


class CustomerResponse(BaseModel):
    """Customer API response.

    Deliberately PERMISSIVE: it must serialize whatever is already stored —
    legacy rows may have a blank name, a non-RFC email, an odd phone, etc. —
    without 500ing the whole list. Strict validation lives on
    CustomerCreate / CustomerUpdate. (email is a plain str here, not EmailStr.)
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_no: Optional[str] = None
    name: Optional[str] = None
    name_ar: Optional[str] = None
    account_type: AccountType = AccountType.RETAIL
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    branch: Optional[str] = None
    relationship_manager: Optional[str] = None
    notes: Optional[str] = None
    status: CustomerStatus = CustomerStatus.ACTIVE
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CustomerListResponse(BaseModel):
    """Paginated envelope for customer list responses."""
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
