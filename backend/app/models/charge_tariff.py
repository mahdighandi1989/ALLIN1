"""Editable Schedule-of-Charges tariff for credit-facility processing fees.

Digitized from the bank's scanned booklet («Schedule of Charges» —
Corporate Ver C01-04-2025 / Individual Ver P01-04-2025). Tariffs change
periodically, so the rules live as DB rows the owner can edit from the UI —
NOT as hardcoded constants. The offer-letter page asks /api/charge-tariff/
compute to auto-fill the processing charges (term 23) from these rules.
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.database import Base


class ChargeRule(Base):
    __tablename__ = "charge_rules"

    id = Column(String(60), primary_key=True)            # stable key, e.g. CR-corporate-line
    segment = Column(String(20), index=True)             # corporate / individual
    rule_key = Column(String(40), index=True)            # see charge_calc.RULE_KEYS
    label = Column(String(200))                          # human label (fa)
    method = Column(String(20))                          # per_mille / percent / flat
    rate = Column(Numeric(10, 4))                        # 4 (per 1000) | 1.5 (%) | flat AED
    min_charge = Column(Numeric(12, 2))                  # floor (nullable)
    max_charge = Column(Numeric(12, 2))                  # cap (nullable)
    # small-amount override (retail personal loan: amount ≤ 10,000 → min 200)
    small_threshold = Column(Numeric(14, 2))
    small_min_charge = Column(Numeric(12, 2))
    notes = Column(Text)                                 # verbatim tariff wording / conditions
    version = Column(String(40))                         # e.g. C01-04-2025
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
