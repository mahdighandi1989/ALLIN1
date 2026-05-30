"""Currency exchange rates (relative to a single base currency).

Rates express how many units of the base currency one unit of ``currency`` is
worth (e.g. base=AED, currency=USD, rate=3.6725 => 1 USD = 3.6725 AED). The base
currency itself has rate 1.0. Editable by an admin; seeded with sensible defaults.
"""
from datetime import datetime

from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.sql import func

from app.database import Base

# The single base/reporting currency for the whole book.
BASE_CURRENCY = "AED"


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    currency = Column(String(3), primary_key=True)         # ISO code, e.g. "USD"
    rate_to_base = Column(Numeric(18, 6), nullable=False)  # 1 <currency> = rate_to_base <BASE>
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<ExchangeRate({self.currency} -> {BASE_CURRENCY} @ {self.rate_to_base})>"


# Seed defaults (approximate, editable in Settings). Base is always 1.0.
DEFAULT_RATES = {
    "AED": "1.0",
    "USD": "3.6725",
    "EUR": "3.95",
    "GBP": "4.65",
    "SAR": "0.98",
    "INR": "0.044",
}
