"""Mortgaged-properties register (read API) — wired at /api/properties.

One backend source for the whole register: the standalone register page AND each
customer's Collateral tab both read from ``mortgaged_properties``. Each row also
carries the owning customer's id (resolved by account_no) so the UI can link a
property straight to its customer.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.profile_entities import MortgagedProperty
from app.models.customer import Customer
from app.utils.security import get_current_user
from app.services.exporters import rows_to_csv

router = APIRouter(tags=["properties"], dependencies=[Depends(get_current_user)])

P = MortgagedProperty


def _conds(search: str, city: str, ptype: str, currency: str):
    conds = [P.is_deleted == False]  # noqa: E712
    if search:
        like = f"%{search.strip()}%"
        conds.append(or_(
            P.account_no.ilike(like), P.customer_name.ilike(like),
            P.mortgage_deed_no.ilike(like), P.city.ilike(like), P.owner.ilike(like),
        ))
    if city:
        conds.append(P.city == city)
    if ptype:
        conds.append(P.prop_type == ptype)
    if currency:
        conds.append(P.valuation_currency == currency)
    return conds


def _row(p: P, customer_id) -> dict:
    return {
        "id": p.id, "ac_no": p.account_no, "customer": p.customer_name, "customer_id": customer_id,
        "deed_no": p.mortgage_deed_no, "city": p.city, "zone": p.zone, "type": p.prop_type,
        "age": p.building_age, "land_m2": p.land_area, "infra_m2": p.infra_area,
        "mortgage_date": p.mortgage_date,
        "amount": float(p.mortgage_amount) if p.mortgage_amount is not None else None,
        "currency": p.valuation_currency, "valuation_date": p.last_valuation_date,
        "valuation": float(p.valuation) if p.valuation is not None else None,
        "owner": p.owner, "insurance_expiry": p.insurance_expiry,
    }


async def _customer_map(db, accounts) -> dict:
    out: dict = {}
    accs = [a for a in accounts if a]
    if accs:
        rows = (await db.execute(
            select(Customer.account_no, Customer.id).where(
                Customer.account_no.in_(accs), Customer.is_deleted == False  # noqa: E712
            )
        )).all()
        for acc, cid in rows:
            out[acc] = cid
    return out


@router.get("/")
async def list_properties(
    db: AsyncSession = Depends(get_db),
    search: str = "", city: str = "", type: str = "", currency: str = "",
    sort_by: str = "customer", sort_order: str = "asc",
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500),
):
    """Filtered, paginated register + totals over the filtered set."""
    conds = _conds(search, city, type, currency)
    total = (await db.execute(select(func.count()).select_from(P).where(*conds))).scalar() or 0
    aed = (await db.execute(
        select(func.coalesce(func.sum(P.valuation), 0)).where(*conds, func.upper(P.valuation_currency) == "AED")
    )).scalar() or 0
    irr = (await db.execute(
        select(func.coalesce(func.sum(P.valuation), 0)).where(*conds, func.upper(P.valuation_currency) == "IRR")
    )).scalar() or 0
    customers = (await db.execute(select(func.count(func.distinct(P.account_no))).where(*conds))).scalar() or 0

    sort_col = {
        "customer": P.customer_name, "ac_no": P.account_no, "city": P.city, "type": P.prop_type,
        "valuation": P.valuation, "amount": P.mortgage_amount,
    }.get(sort_by, P.customer_name)
    sort_col = sort_col.desc() if sort_order == "desc" else sort_col.asc()

    items = (await db.execute(
        select(P).where(*conds).order_by(sort_col).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    cmap = await _customer_map(db, {p.account_no for p in items})

    return {
        "items": [_row(p, cmap.get(p.account_no)) for p in items],
        "total": total, "page": page, "page_size": page_size,
        "totals": {"aed": float(aed), "irr": float(irr), "customers": customers},
    }


@router.get("/facets")
async def property_facets(db: AsyncSession = Depends(get_db)):
    """Distinct cities + types for the filter dropdowns."""
    cities = [c for (c,) in (await db.execute(
        select(P.city).where(P.is_deleted == False, P.city != "").distinct().order_by(P.city)  # noqa: E712
    )).all() if c]
    types = [t for (t,) in (await db.execute(
        select(P.prop_type).where(P.is_deleted == False, P.prop_type != "").distinct().order_by(P.prop_type)  # noqa: E712
    )).all() if t]
    return {"cities": cities, "types": types}


@router.get("/export.csv")
async def export_properties_csv(
    db: AsyncSession = Depends(get_db),
    search: str = "", city: str = "", type: str = "", currency: str = "",
):
    conds = _conds(search, city, type, currency)
    rows = (await db.execute(select(P).where(*conds).order_by(P.customer_name))).scalars().all()
    headers = ["Account", "Customer", "Deed No", "City", "Zone", "Type", "Age", "Land m2", "Infra m2",
               "Mortgage Date", "Amount", "Currency", "Valuation Date", "Valuation", "Owner", "Insurance Expiry"]
    data = [[
        p.account_no, p.customer_name, p.mortgage_deed_no, p.city, p.zone, p.prop_type, p.building_age,
        p.land_area, p.infra_area, p.mortgage_date,
        float(p.mortgage_amount) if p.mortgage_amount is not None else "",
        p.valuation_currency, p.last_valuation_date,
        float(p.valuation) if p.valuation is not None else "", p.owner, p.insurance_expiry,
    ] for p in rows]
    return Response(
        content=rows_to_csv(headers, data), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="mortgaged-properties.csv"'},
    )
