from sqlalchemy import Column, Integer, String, Numeric, Date, Enum, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import enum
from ..database import Base
from ..utils.id_generator import generate_facility_id


class FacilityType(str, enum.Enum):
    LOAN = "loan"
    OVERDRAFT = "overdraft"
    LC = "lc"
    LG = "lg"
    OTHER = "other"


class FacilityStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"
    CLOSED = "closed"
    DEFAULTED = "defaulted"
    WRITTEN_OFF = "written_off"


class RiskRating(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# The set of accepted risk_rating string values (lowercased).
RISK_RATINGS = {r.value for r in RiskRating}
DEFAULT_RISK_RATING = RiskRating.LOW.value


# Persist the enum *value* (e.g. "loan"), not the member NAME ("LOAN"), so the
# stored data matches the API strings and == filters work. See the same note in
# models/customer.py.
def _enum_col(enum_cls, **kw):
    return Column(
        Enum(enum_cls, values_callable=lambda e: [m.value for m in e]), **kw
    )


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(33), primary_key=True, index=True, default=generate_facility_id)
    customer_id = Column(String(33), ForeignKey("customers.id"), nullable=False)
    name = Column(String(200))
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="AED")
    facility_type = _enum_col(FacilityType, default=FacilityType.LOAN)
    start_date = Column(Date)
    end_date = Column(Date)
    expiry_date = Column(Date)
    outstanding = Column(Numeric(15, 2), default=0)
    status = _enum_col(FacilityStatus, default=FacilityStatus.ACTIVE)
    purpose = Column(String(500))
    tenor_months = Column(String(4))
    notes = Column(Text)
    interest_rate = Column(Numeric(5, 2))
    collateral_value = Column(Numeric(15, 2))
    # risk_rating is constrained to the RiskRating set (low/medium/high) by the
    # @validates hook below — every write path (API, import, seed) is checked.
    # The column stays a String (not a DB ENUM) on purpose: it avoids a
    # destructive type migration on the live Postgres DB while still being
    # validated at the ORM layer. It is NOT NULL and defaults to 'low'.
    risk_rating = Column(String(10), nullable=False, default=DEFAULT_RISK_RATING)
    relationship_manager = Column(String(255))
    branch = Column(String(100))
    approved_by = Column(String(255))
    approved_date = Column(Date)
    reviewed_date = Column(Date)
    next_review_date = Column(Date)
    comments = Column(String(1000))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="facilities")

    @validates("risk_rating")
    def _validate_risk_rating(self, key, value):
        """Constrain risk_rating to the RiskRating set.

        Accepts a RiskRating member or a (case-insensitive) string; a blank/None
        value falls back to the default. An unknown value raises ValueError so an
        out-of-range rating is rejected at write time rather than silently stored.
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return DEFAULT_RISK_RATING
        normalised = (value.value if isinstance(value, RiskRating) else str(value)).strip().lower()
        if normalised not in RISK_RATINGS:
            raise ValueError(
                f"invalid risk_rating '{value}' (expected one of {sorted(RISK_RATINGS)})"
            )
        return normalised

    def __init__(self, **kwargs):
        # Construction-time defaults (column ``default=`` only applies on INSERT).
        kwargs.setdefault("status", FacilityStatus.ACTIVE)
        kwargs.setdefault("currency", "AED")
        kwargs.setdefault("outstanding", 0)
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    def __repr__(self):
        return (
            f"<Facility(id={self.id}, customer_id={self.customer_id}, "
            f"type={getattr(self.facility_type, 'value', self.facility_type)}, "
            f"amount={self.amount}, currency={self.currency}, "
            f"status={getattr(self.status, 'value', self.status)})>"
        )

    def __str__(self):
        ftype = getattr(self.facility_type, "value", self.facility_type)
        base = f"Facility {self.id} - {ftype}"
        if self.name:
            base += f" - {self.name}"
        return base


# برای backward compatibility
__all__ = ["Facility", "FacilityType", "FacilityStatus", "RiskRating", "RISK_RATINGS"]