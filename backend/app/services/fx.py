"""Currency conversion helpers built on the exchange_rates table.

Everything in the book is normalised to a single BASE_CURRENCY for aggregation
(dashboard totals, reports). A facility stored in USD is converted to AED using
its rate before being summed, so portfolio figures are apples-to-apples.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict

import sqlalchemy as sa

from app.database import AsyncSessionLocal
from app.models.exchange_rate import ExchangeRate, BASE_CURRENCY, DEFAULT_RATES

logger = logging.getLogger(__name__)

# Currencies already warned about this process — one loud line per currency,
# not one per converted amount (to_base runs inside aggregation loops).
_WARNED_UNKNOWN: set = set()


async def load_rates(db=None) -> Dict[str, float]:
    """Return {currency: rate_to_base}. Falls back to DEFAULT_RATES on any error.

    The base currency is always present with rate 1.0.
    """
    rates: Dict[str, float] = {BASE_CURRENCY: 1.0}
    try:
        if db is not None:
            rows = (await db.execute(sa.select(ExchangeRate))).scalars().all()
        else:
            async with AsyncSessionLocal() as session:
                rows = (await session.execute(sa.select(ExchangeRate))).scalars().all()
        for r in rows:
            try:
                rates[r.currency.upper()] = float(r.rate_to_base)
            except (TypeError, ValueError):
                continue
        if len(rates) <= 1:
            # Reachable-but-empty table: without this, every foreign-currency
            # amount would silently convert 1:1 below. Use the defaults and
            # say so.
            logger.warning("FX rate table is empty; falling back to DEFAULT_RATES")
            for k, v in DEFAULT_RATES.items():
                rates.setdefault(k, float(v))
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.warning("FX rate load failed, using defaults: %s", exc)
        for k, v in DEFAULT_RATES.items():
            rates.setdefault(k, float(v))
    rates[BASE_CURRENCY] = 1.0
    return rates


def to_base(amount, currency: str, rates: Dict[str, float]) -> float:
    """Convert ``amount`` in ``currency`` to the base currency using ``rates``."""
    if amount is None:
        return 0.0
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        return 0.0
    cur = (currency or BASE_CURRENCY).upper()
    rate = rates.get(cur)
    if rate is None:
        # Unknown currency: assume it is already base (1:1) rather than
        # dropping it — but NEVER silently: a missing USD rate misstates
        # exposure ~3.67x on the dashboard. Warn once per currency.
        if cur not in _WARNED_UNKNOWN:
            _WARNED_UNKNOWN.add(cur)
            logger.warning(
                "FX: no rate for currency %r — converting 1:1 to %s. "
                "Add the rate in Settings to fix exposure figures.",
                cur, BASE_CURRENCY,
            )
        rate = 1.0
    return amt * rate


async def seed_default_rates() -> None:
    """Insert the default rate table the first time (idempotent)."""
    try:
        async with AsyncSessionLocal() as session:
            count = (
                await session.execute(sa.select(sa.func.count(ExchangeRate.currency)))
            ).scalar() or 0
            if count:
                return
            for cur, rate in DEFAULT_RATES.items():
                session.add(ExchangeRate(currency=cur.upper(), rate_to_base=Decimal(rate)))
            await session.commit()
            logger.info("Seeded %s default exchange rates", len(DEFAULT_RATES))
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.error("Default FX seeding skipped: %s", exc)
