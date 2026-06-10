from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.schemas.facility import (
    FacilityCreate,
    FacilityUpdate,
    FacilityResponse,
    FacilityListResponse,
)
from app.routers.auth import require_editor
from app.services.audit import record_audit
from app.services.checklist import seed_facility_checklist
from app.services.exporters import rows_to_csv, build_xlsx, XLSX_MEDIA_TYPE
from app.services.facility_authorization import require_facility_reader

# Authentication AND read-authorization are required for every facility endpoint.
# ``require_facility_reader`` (app.services.facility_authorization) first resolves
# the caller via get_current_user, then makes the authorization decision explicit
# and centralised: only an approved account (viewer/editor/admin) may read
# facility data; an authenticated-but-pending account gets 403. Write endpoints
# additionally depend on ``require_editor``. The prefix is provided by main.py
# (/api/facilities), so the router itself must not add another prefix.
router = APIRouter(
    tags=["facilities"], dependencies=[Depends(require_facility_reader)]
)

_FACILITY_NOT_FOUND = "Facility not found"
_CUSTOMER_NOT_FOUND = "Customer not found"


async def _get_active_facility(facility_id: str, db: AsyncSession) -> Facility:
    """Fetch a non-deleted facility or raise 404 (with a stable message)."""
    result = await db.execute(
        select(Facility).where(
            Facility.id == facility_id, Facility.is_deleted == False
        )
    )
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_FACILITY_NOT_FOUND
        )
    return facility


async def _ensure_customer_exists(customer_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id, Customer.is_deleted == False
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_CUSTOMER_NOT_FOUND
        )


_FACILITY_SORT = {
    "name": Facility.name,
    "amount": Facility.amount,
    "outstanding": Facility.outstanding,
    "created_at": Facility.created_at,
    "expiry_date": Facility.expiry_date,
    "status": Facility.status,
    "facility_type": Facility.facility_type,
}


@router.get("/", response_model=FacilityListResponse)
async def list_facilities(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    facility_type: Optional[FacilityType] = Query(None, description="Filter by facility type"),
    status: Optional[FacilityStatus] = Query(None, description="Filter by facility status"),
    search: Optional[str] = Query(None, description="Search term for facility name"),
    amount_min: Optional[float] = Query(None, ge=0, description="Minimum amount"),
    amount_max: Optional[float] = Query(None, ge=0, description="Maximum amount"),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="asc or desc"),
):
    """Retrieve a paginated, filterable, sortable list of facilities."""
    base = select(Facility).where(Facility.is_deleted == False)

    if customer_id:
        base = base.where(Facility.customer_id == customer_id)
    if facility_type:
        base = base.where(Facility.facility_type == facility_type)
    if status:
        base = base.where(Facility.status == status)
    if search:
        base = base.where(Facility.name.ilike(f"%{search}%"))
    if amount_min is not None:
        base = base.where(Facility.amount >= amount_min)
    if amount_max is not None:
        base = base.where(Facility.amount <= amount_max)

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    sort_col = _FACILITY_SORT.get(sort_by, Facility.created_at)
    sort_col = sort_col.asc() if sort_order == "asc" else sort_col.desc()

    result = await db.execute(
        base.order_by(sort_col).offset((page - 1) * page_size).limit(page_size)
    )
    facilities = result.scalars().all()

    return FacilityListResponse(
        items=facilities, total=total, page=page, page_size=page_size
    )


_FACILITY_EXPORT_HEADERS = [
    "id", "customer_id", "name", "facility_type", "status",
    "amount", "outstanding", "currency", "interest_rate", "expiry_date",
]


async def _facilities_for_export(
    db, search, facility_type, status, amount_min, amount_max,
    sort_by="created_at", sort_order="desc",
):
    base = select(Facility).where(Facility.is_deleted == False)
    if search:
        base = base.where(Facility.name.ilike(f"%{search}%"))
    if facility_type:
        base = base.where(Facility.facility_type == facility_type)
    if status:
        base = base.where(Facility.status == status)
    if amount_min is not None:
        base = base.where(Facility.amount >= amount_min)
    if amount_max is not None:
        base = base.where(Facility.amount <= amount_max)
    # Honour the same sort the list view applies so the exported file matches
    # exactly what the user sees on screen. Unknown columns fall back to
    # created_at and any non-"asc" order is treated as descending.
    sort_col = _FACILITY_SORT.get(sort_by, Facility.created_at)
    sort_col = sort_col.asc() if sort_order == "asc" else sort_col.desc()
    rows = (await db.execute(base.order_by(sort_col).limit(10000))).scalars().all()
    return [
        [f.id, f.customer_id, f.name,
         getattr(f.facility_type, "value", f.facility_type),
         getattr(f.status, "value", f.status),
         float(f.amount or 0), float(f.outstanding or 0), f.currency,
         float(f.interest_rate) if f.interest_rate is not None else None,
         f.expiry_date.isoformat() if f.expiry_date else None]
        for f in rows
    ]


@router.get("/export.csv")
async def export_facilities_csv(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None),
    facility_type: Optional[FacilityType] = Query(None),
    status: Optional[FacilityStatus] = Query(None),
    amount_min: Optional[float] = Query(None, ge=0),
    amount_max: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="asc or desc"),
):
    rows = await _facilities_for_export(
        db, search, facility_type, status, amount_min, amount_max, sort_by, sort_order
    )
    return Response(
        content=rows_to_csv(_FACILITY_EXPORT_HEADERS, rows),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="facilities.csv"'},
    )


@router.get("/export.xlsx")
async def export_facilities_xlsx(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None),
    facility_type: Optional[FacilityType] = Query(None),
    status: Optional[FacilityStatus] = Query(None),
    amount_min: Optional[float] = Query(None, ge=0),
    amount_max: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="asc or desc"),
):
    rows = await _facilities_for_export(
        db, search, facility_type, status, amount_min, amount_max, sort_by, sort_order
    )
    content = build_xlsx([("Facilities", _FACILITY_EXPORT_HEADERS, rows)])
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="facilities.xlsx"'},
    )


class BulkIds(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=500)


@router.post("/bulk/delete")
async def bulk_delete_facilities(
    payload: BulkIds,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Soft-delete many facilities at once."""
    result = await db.execute(
        update(Facility)
        .where(Facility.id.in_(payload.ids), Facility.is_deleted == False)
        .values(is_deleted=True)
    )
    await db.commit()
    affected = result.rowcount or 0
    await record_audit(
        action="delete", entity_type="facility", entity_id=f"bulk:{affected}",
        detail=f"Bulk-deleted {affected} facilities ({len(payload.ids)} requested)",
        user=current_user, request=request, db=db,
    )
    return {"deleted": affected}


# Internal/extended search surface: richer than the main ``GET /`` list (adds
# start-date range + customer-name filtering) but not yet wired to the SPA, which
# uses the list endpoint's filters. Kept functional for API/admin consumers but
# hidden from the public OpenAPI schema (unused-endpoint audit, see
# docs/ENDPOINT_AUDIT.md).
@router.get(
    "/search/advanced",
    response_model=FacilityListResponse,
    include_in_schema=False,
)
async def advanced_search_facilities(
    db: AsyncSession = Depends(get_db),
    amount_from: Optional[float] = Query(None, ge=0),
    amount_to: Optional[float] = Query(None, ge=0),
    date_from: Optional[date] = Query(None, description="Earliest start date"),
    date_to: Optional[date] = Query(None, description="Latest start date"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    facility_type: Optional[FacilityType] = Query(None),
    status: Optional[FacilityStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
):
    """Advanced facility search by amount range, start-date range and customer name."""
    base = select(Facility).where(Facility.is_deleted == False)

    if amount_from is not None:
        base = base.where(Facility.amount >= amount_from)
    if amount_to is not None:
        base = base.where(Facility.amount <= amount_to)
    if date_from is not None:
        base = base.where(Facility.start_date >= date_from)
    if date_to is not None:
        base = base.where(Facility.start_date <= date_to)
    if facility_type:
        base = base.where(Facility.facility_type == facility_type)
    if status:
        base = base.where(Facility.status == status)
    if customer_name:
        customer_ids = select(Customer.id).where(
            Customer.name.ilike(f"%{customer_name}%")
        )
        base = base.where(Facility.customer_id.in_(customer_ids))

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(Facility.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    facilities = result.scalars().all()
    return FacilityListResponse(
        items=facilities, total=total, page=page, page_size=page_size
    )


@router.get("/{facility_id}/detail")
async def get_facility_detail(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Full facility profile: the facility plus its customer's name/account."""
    facility = await _get_active_facility(facility_id, db)
    cust = (
        await db.execute(
            select(Customer.name, Customer.account_no).where(
                Customer.id == facility.customer_id
            )
        )
    ).first()
    return {
        "facility": FacilityResponse.model_validate(facility),
        "customer_name": cust[0] if cust else None,
        "customer_account_no": cust[1] if cust else None,
    }


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific facility by ID."""
    return await _get_active_facility(facility_id, db)


@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
async def create_facility(
    facility_data: FacilityCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Create a new facility (after verifying the owning customer exists)."""
    await _ensure_customer_exists(facility_data.customer_id, db)

    new_facility = Facility(**facility_data.model_dump())
    db.add(new_facility)
    await db.commit()
    await db.refresh(new_facility)
    # A24: seed the new facility's own credit-file checklist with hourglasses.
    acc = (
        await db.execute(select(Customer.account_no).where(Customer.id == new_facility.customer_id))
    ).scalar_one_or_none() or ""
    await seed_facility_checklist(db, acc, new_facility.id, getattr(current_user, "username", "") or "")
    await db.commit()
    await record_audit(
        action="create", entity_type="facility", entity_id=new_facility.id,
        detail=f"Created facility '{new_facility.name or new_facility.id}'",
        user=current_user, request=request, db=db,
    )
    return new_facility


@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: str,
    facility_data: FacilityUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Update an existing facility."""
    facility = await _get_active_facility(facility_id, db)

    update_data = facility_data.model_dump(exclude_unset=True)
    if (
        update_data.get("customer_id")
        and update_data["customer_id"] != facility.customer_id
    ):
        await _ensure_customer_exists(update_data["customer_id"], db)

    for field, value in update_data.items():
        setattr(facility, field, value)

    await db.commit()
    await db.refresh(facility)
    await record_audit(
        action="update", entity_type="facility", entity_id=facility.id,
        detail=f"Updated facility '{facility.name or facility.id}'",
        user=current_user, request=request, db=db,
    )
    return facility


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facility(
    facility_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Soft delete a facility."""
    facility = await _get_active_facility(facility_id, db)
    facility.is_deleted = True
    await db.commit()
    await record_audit(
        action="delete", entity_type="facility", entity_id=facility.id,
        detail=f"Deleted facility '{facility.name or facility.id}'",
        user=current_user, request=request, db=db,
    )
    return None


@router.post("/{facility_id}/restore", response_model=FacilityResponse)
async def restore_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    """Restore a previously soft-deleted facility and re-activate it."""
    result = await db.execute(
        select(Facility).where(
            Facility.id == facility_id, Facility.is_deleted == True
        )
    )
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_FACILITY_NOT_FOUND
        )

    facility.is_deleted = False
    facility.status = FacilityStatus.ACTIVE
    await db.commit()
    await db.refresh(facility)
    return facility


@router.patch("/{facility_id}/status")
async def update_facility_status(
    facility_id: str,
    new_status: FacilityStatus = Query(..., description="New facility status"),
    db: AsyncSession = Depends(get_db),
):
    """Update only the status of a facility."""
    facility = await _get_active_facility(facility_id, db)
    facility.status = new_status
    await db.commit()
    await db.refresh(facility)
    return {
        "message": f"Facility status updated to {new_status.value}",
        "id": facility.id,
        "status": facility.status.value,
    }
