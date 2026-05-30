"""Portfolio reporting endpoints (read-only analytics over the whole book)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, cast as sa_cast, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility
from app.utils.security import get_current_user

router = APIRouter(tags=["reports"], dependencies=[Depends(get_current_user)])


async def _grouped(db: AsyncSession, model, column, *, amount_col=None):
    cols = [column, func.count(model.id)]
    if amount_col is not None:
        cols.append(func.coalesce(func.sum(sa_cast(amount_col, Float)), 0.0))
    rows = (
        await db.execute(
            select(*cols).where(model.is_deleted == False).group_by(column)
        )
    ).all()
    out = []
    for r in rows:
        label = getattr(r[0], "value", r[0])
        out.append({
            "label": str(label) if label is not None else "unknown",
            "count": int(r[1] or 0),
            "amount": float(r[2]) if amount_col is not None and len(r) > 2 else 0.0,
        })
    out.sort(key=lambda x: x["amount"] or x["count"], reverse=True)
    return out


@router.get("/portfolio")
async def portfolio_report(db: AsyncSession = Depends(get_db)):
    """A consolidated portfolio report used by the Reports page."""
    total_customers = (
        await db.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
    ).scalar() or 0
    total_facilities = (
        await db.execute(
            select(func.count(Facility.id)).where(Facility.is_deleted == False)
        )
    ).scalar() or 0
    total_exposure = float(
        (
            await db.execute(
                select(func.coalesce(func.sum(sa_cast(Facility.amount, Float)), 0.0))
                .where(Facility.is_deleted == False)
            )
        ).scalar()
        or 0
    )
    total_outstanding = float(
        (
            await db.execute(
                select(func.coalesce(func.sum(sa_cast(Facility.outstanding, Float)), 0.0))
                .where(Facility.is_deleted == False)
            )
        ).scalar()
        or 0
    )

    by_type = await _grouped(db, Facility, Facility.facility_type, amount_col=Facility.amount)
    by_status = await _grouped(db, Facility, Facility.status, amount_col=Facility.amount)
    by_risk = await _grouped(db, Facility, Facility.risk_rating, amount_col=Facility.amount)
    by_branch = await _grouped(db, Customer, Customer.branch, amount_col=None)
    by_customer_type = await _grouped(db, Customer, Customer.account_type, amount_col=None)

    utilisation = (total_outstanding / total_exposure * 100) if total_exposure else 0.0

    return {
        "summary": {
            "total_customers": total_customers,
            "total_facilities": total_facilities,
            "total_exposure": total_exposure,
            "total_outstanding": total_outstanding,
            "available_headroom": max(0.0, total_exposure - total_outstanding),
            "utilisation_pct": round(utilisation, 1),
            "currency": "AED",
        },
        "facilities_by_type": by_type,
        "facilities_by_status": by_status,
        "facilities_by_risk": by_risk,
        "customers_by_branch": by_branch,
        "customers_by_type": by_customer_type,
    }


@router.get("/top-exposures")
async def top_exposures(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """The largest customer exposures (sum of facility amounts), descending."""
    rows = (
        await db.execute(
            select(
                Customer.id,
                Customer.name,
                Customer.account_no,
                func.coalesce(func.sum(sa_cast(Facility.amount, Float)), 0.0).label("exposure"),
                func.count(Facility.id).label("facilities"),
            )
            .join(Facility, and_(
                Facility.customer_id == Customer.id, Facility.is_deleted == False
            ), isouter=True)
            .where(Customer.is_deleted == False)
            .group_by(Customer.id, Customer.name, Customer.account_no)
            .order_by(func.coalesce(func.sum(sa_cast(Facility.amount, Float)), 0.0).desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "customer_id": r[0],
                "name": r[1],
                "account_no": r[2],
                "exposure": float(r[3] or 0),
                "facilities": int(r[4] or 0),
            }
            for r in rows
        ]
    }
