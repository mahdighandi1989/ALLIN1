"""Mortgaged-properties register (read API) — wired at /api/properties.

One backend source for the whole register: the standalone register page AND each
customer's Collateral tab both read from ``mortgaged_properties``. Each row also
carries the owning customer's id (resolved by account_no) so the UI can link a
property straight to its customer.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.profile_entities import MortgagedProperty
from app.models.customer import Customer
from app.utils.security import get_current_user
from app.routers.auth import require_editor
from app.services.customer_link import ensure_customer
from app.services.exporters import rows_to_csv

router = APIRouter(tags=["properties"], dependencies=[Depends(get_current_user)])

P = MortgagedProperty

# Fields a client may write directly (account_no/customer_name handled explicitly).
_WRITABLE = {
    "facility_id", "country", "plate_no", "mortgage_deed_no", "city", "address",
    "prop_type", "building_age", "land_area", "cnbc", "zone", "infra_area", "owner",
    "valuation", "valuation_currency", "insurance_expiry", "insurance_no",
    "last_valuation_date", "mortgage_date", "mortgage_amount", "remarks",
    # v58 columns that never made it into the manual-edit whitelist + the v110
    # insurance-policy identity block (the owner's collateral table)
    "owner_national_id", "postal_code", "insurance_issue", "insurance_computer_code",
    "insurance_policyholder", "insurance_subject", "insurance_activity",
    "insurance_coverage_total", "insurance_issuing_unit",
    # v116 — the rest of the printed policy page
    "insurance_unique_code", "insurance_beneficiary", "insurance_premium_total",
    "insurance_perils", "insurance_type",
}
_NUMERIC = {"valuation", "mortgage_amount"}


def _apply(obj: P, data: dict) -> None:
    cols = obj.__table__.columns
    for k, v in data.items():
        if k not in _WRITABLE or v is None:
            continue
        if k in _NUMERIC:
            setattr(obj, k, v)
            continue
        col = cols.get(k)
        maxlen = getattr(getattr(col, "type", None), "length", None) if col is not None else None
        s = str(v)
        setattr(obj, k, s[:maxlen] if maxlen else s)


class PropertyWrite(BaseModel):
    account_no: str
    customer_name: str = ""
    facility_id: str = ""
    country: str = ""
    plate_no: str = ""
    mortgage_deed_no: str = ""
    city: str = ""
    address: str = ""
    prop_type: str = ""
    building_age: str = ""
    land_area: str = ""
    cnbc: str = ""
    zone: str = ""
    infra_area: str = ""
    owner: str = ""
    valuation: Optional[float] = None
    valuation_currency: str = "AED"
    insurance_expiry: str = ""
    insurance_no: str = ""
    last_valuation_date: str = ""
    mortgage_date: str = ""
    mortgage_amount: Optional[float] = None
    remarks: str = ""
    owner_national_id: str = ""
    postal_code: str = ""
    insurance_issue: str = ""
    insurance_computer_code: str = ""
    insurance_policyholder: str = ""
    insurance_subject: str = ""
    insurance_activity: str = ""
    insurance_coverage_total: str = ""
    insurance_issuing_unit: str = ""
    insurance_unique_code: str = ""
    insurance_beneficiary: str = ""
    insurance_premium_total: str = ""
    insurance_perils: str = ""
    insurance_type: str = ""


class PropertyPatch(BaseModel):
    customer_name: Optional[str] = None
    facility_id: Optional[str] = None
    country: Optional[str] = None
    plate_no: Optional[str] = None
    mortgage_deed_no: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    prop_type: Optional[str] = None
    building_age: Optional[str] = None
    land_area: Optional[str] = None
    cnbc: Optional[str] = None
    zone: Optional[str] = None
    infra_area: Optional[str] = None
    owner: Optional[str] = None
    valuation: Optional[float] = None
    valuation_currency: Optional[str] = None
    insurance_expiry: Optional[str] = None
    insurance_no: Optional[str] = None
    last_valuation_date: Optional[str] = None
    mortgage_date: Optional[str] = None
    mortgage_amount: Optional[float] = None
    remarks: Optional[str] = None
    owner_national_id: Optional[str] = None
    postal_code: Optional[str] = None
    insurance_issue: Optional[str] = None
    insurance_computer_code: Optional[str] = None
    insurance_policyholder: Optional[str] = None
    insurance_subject: Optional[str] = None
    insurance_activity: Optional[str] = None
    insurance_coverage_total: Optional[str] = None
    insurance_issuing_unit: Optional[str] = None
    insurance_unique_code: Optional[str] = None
    insurance_beneficiary: Optional[str] = None
    insurance_premium_total: Optional[str] = None
    insurance_perils: Optional[str] = None
    insurance_type: Optional[str] = None


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
        "facility_id": p.facility_id, "deed_no": p.mortgage_deed_no, "city": p.city,
        "zone": p.zone, "type": p.prop_type,
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


# ---------------------------------------------------------------------------
# Create / edit / delete directly from the register (not only from a customer's
# profile). Creating ensures the owning customer exists — an orphan account_no
# gets a stub profile so the property is always reachable from a customer.
# ---------------------------------------------------------------------------
def _detail(p: P) -> dict:
    """Full row (every column) for the edit form / after a write."""
    out = {}
    for col in p.__table__.columns:
        if col.name == "created_at":
            continue
        v = getattr(p, col.name)
        out[col.name] = float(v) if isinstance(v, Decimal) else v
    return out


@router.post("/", status_code=201)
async def create_property(
    payload: PropertyWrite,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Add a property to the register, linking (and if needed creating) its customer."""
    account_no = (payload.account_no or "").strip()
    if not account_no:
        raise HTTPException(status_code=422, detail="account_no is required")
    customer = await ensure_customer(db, account_no, payload.customer_name)
    data = payload.model_dump(exclude_unset=True)
    obj = P(
        id=f"PROP-{account_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:3]}",
        account_no=account_no,
        customer_name=(payload.customer_name or (customer.name if customer else "") or "")[:200],
        date_added=date.today().isoformat(),
        created_by=getattr(user, "username", "") or "",
    )
    _apply(obj, data)
    db.add(obj)
    await db.commit()
    return _detail(obj)


@router.put("/{item_id}")
async def update_property(
    item_id: str,
    payload: PropertyPatch,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Edit a property in the register."""
    obj = (await db.execute(select(P).where(P.id == item_id))).scalar_one_or_none()
    if obj is None or obj.is_deleted:
        raise HTTPException(status_code=404, detail="Property not found")
    data = payload.model_dump(exclude_unset=True)
    if "customer_name" in data and data["customer_name"] is not None:
        obj.customer_name = str(data["customer_name"])[:200]
    _apply(obj, data)
    await db.commit()
    return _detail(obj)


@router.delete("/{item_id}")
async def delete_property(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    """Soft-delete a property from the register."""
    obj = (await db.execute(select(P).where(P.id == item_id))).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Property not found")
    obj.is_deleted = True
    await db.commit()
    return {"ok": True, "id": item_id, "deleted": True}
