"""Currency / exchange-rate management."""
from typing import Dict, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.exchange_rate import ExchangeRate, BASE_CURRENCY
from app.routers.auth import require_admin
from app.services.audit import record_audit
from app.services.fx import load_rates, to_base
from app.utils.security import get_current_user

router = APIRouter(tags=["fx"], dependencies=[Depends(get_current_user)])

_CCY_RE = __import__("re").compile(r"^[A-Za-z]{3}$")


class RateItem(BaseModel):
    currency: str
    rate_to_base: float


class RatesUpdate(BaseModel):
    rates: Dict[str, float]


@router.get("/")
async def list_rates(db: AsyncSession = Depends(get_db)):
    """All exchange rates (rate_to_base) plus the base currency."""
    rows = (await db.execute(select(ExchangeRate).order_by(ExchangeRate.currency))).scalars().all()
    return {
        "base_currency": BASE_CURRENCY,
        "rates": [{"currency": r.currency, "rate_to_base": float(r.rate_to_base)} for r in rows],
    }


@router.put("/")
async def update_rates(
    payload: RatesUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    """Upsert exchange rates (admin only). Currency must be a 3-letter code."""
    if not payload.rates:
        raise HTTPException(status_code=422, detail="No rates supplied")
    for cur, rate in payload.rates.items():
        if not _CCY_RE.match(cur):
            raise HTTPException(status_code=422, detail=f"Invalid currency code '{cur}'")
        if rate <= 0:
            raise HTTPException(status_code=422, detail=f"Rate for '{cur}' must be positive")

    for cur, rate in payload.rates.items():
        code = cur.upper()
        existing = (
            await db.execute(select(ExchangeRate).where(ExchangeRate.currency == code))
        ).scalar_one_or_none()
        if existing:
            existing.rate_to_base = Decimal(str(rate))
        else:
            db.add(ExchangeRate(currency=code, rate_to_base=Decimal(str(rate))))
    # The base currency must always be 1.0.
    base = (
        await db.execute(select(ExchangeRate).where(ExchangeRate.currency == BASE_CURRENCY))
    ).scalar_one_or_none()
    if base:
        base.rate_to_base = Decimal("1.0")

    await db.commit()
    await record_audit(
        action="update", entity_type="exchange_rate",
        entity_id=",".join(sorted(payload.rates))[:64],
        detail=f"Updated rates: {sorted(payload.rates)}", user=actor, request=request, db=db,
    )
    return await list_rates(db=db)


@router.get("/convert")
async def convert(
    amount: float,
    from_currency: str,
    to_currency: str = BASE_CURRENCY,
    db: AsyncSession = Depends(get_db),
):
    """Convert an amount between two currencies via the base currency."""
    rates = await load_rates(db)
    base_amount = to_base(amount, from_currency, rates)
    to_rate = rates.get(to_currency.upper(), 1.0) or 1.0
    converted = base_amount / to_rate
    return {
        "amount": amount,
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "converted": round(converted, 2),
        "base_currency": BASE_CURRENCY,
    }
