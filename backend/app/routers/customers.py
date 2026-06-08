from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import and_, or_, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility
from app.models.offer_letter import OfferLetter
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
)
from app.schemas.facility import FacilityResponse
from app.schemas.offer_letter import OfferLetterResponse
from app.utils.security import get_current_user
from app.routers.auth import require_editor
from app.services.audit import record_audit
from app.services.exporters import rows_to_csv, build_xlsx, XLSX_MEDIA_TYPE

# Authentication is required for every customer endpoint (reads allowed for any
# approved user; writes are gated to editor/admin via require_editor below).
router = APIRouter(tags=["customers"], dependencies=[Depends(get_current_user)])

_CUSTOMER_NOT_FOUND = "Customer not found"


async def _get_active_customer(customer_id: str, db: AsyncSession) -> Customer:
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id, Customer.is_deleted == False
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_CUSTOMER_NOT_FOUND
        )
    return customer


# Columns clients may sort by (maps API name -> model column).
_CUSTOMER_SORT = {
    "name": Customer.name,
    "account_no": Customer.account_no,
    "created_at": Customer.created_at,
    "status": Customer.status,
    "account_type": Customer.account_type,
}


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search name / account no / email"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="asc or desc"),
):
    """Paginated, filterable, sortable list of customers.

    ``search`` matches name, account number or email case-insensitively. The
    term is always parameterised (never string-formatted into SQL), so special
    characters are treated as literals.
    """
    base = select(Customer).where(Customer.is_deleted == False)

    if search:
        like = f"%{search}%"
        base = base.where(
            or_(
                Customer.name.ilike(like),
                Customer.account_no.ilike(like),
                Customer.email.ilike(like),
            )
        )
    if account_type:
        base = base.where(Customer.account_type == account_type)
    if status:
        base = base.where(Customer.status == status)
    if branch:
        base = base.where(Customer.branch.ilike(f"%{branch}%"))

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    sort_col = _CUSTOMER_SORT.get(sort_by, Customer.created_at)
    sort_col = sort_col.asc() if sort_order == "asc" else sort_col.desc()

    result = await db.execute(
        base.order_by(sort_col).offset((page - 1) * page_size).limit(page_size)
    )
    customers = result.scalars().all()

    return CustomerListResponse(
        items=customers, total=total, page=page, page_size=page_size
    )


_CUSTOMER_EXPORT_HEADERS = [
    "id", "account_no", "name", "account_type", "status",
    "email", "phone", "branch", "relationship_manager",
]


async def _customers_for_export(db, search, account_type, status, branch):
    base = select(Customer).where(Customer.is_deleted == False)
    if search:
        like = f"%{search}%"
        base = base.where(or_(
            Customer.name.ilike(like), Customer.account_no.ilike(like), Customer.email.ilike(like)
        ))
    if account_type:
        base = base.where(Customer.account_type == account_type)
    if status:
        base = base.where(Customer.status == status)
    if branch:
        base = base.where(Customer.branch.ilike(f"%{branch}%"))
    rows = (await db.execute(base.order_by(Customer.created_at.desc()).limit(10000))).scalars().all()
    return [
        [c.id, c.account_no, c.name,
         getattr(c.account_type, "value", c.account_type),
         getattr(c.status, "value", c.status),
         c.email, c.phone, c.branch, c.relationship_manager]
        for c in rows
    ]


@router.get("/export.csv")
async def export_customers_csv(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None),
    account_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
):
    rows = await _customers_for_export(db, search, account_type, status, branch)
    return Response(
        content=rows_to_csv(_CUSTOMER_EXPORT_HEADERS, rows),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="customers.csv"'},
    )


@router.get("/export.xlsx")
async def export_customers_xlsx(
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None),
    account_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
):
    rows = await _customers_for_export(db, search, account_type, status, branch)
    content = build_xlsx([("Customers", _CUSTOMER_EXPORT_HEADERS, rows)])
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="customers.xlsx"'},
    )


class BulkIds(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=500)


@router.post("/bulk/delete")
async def bulk_delete_customers(
    payload: BulkIds,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Soft-delete many customers at once. Returns how many were affected."""
    result = await db.execute(
        update(Customer)
        .where(Customer.id.in_(payload.ids), Customer.is_deleted == False)
        .values(is_deleted=True)
    )
    await db.commit()
    affected = result.rowcount or 0
    await record_audit(
        action="delete", entity_type="customer", entity_id=f"bulk:{affected}",
        detail=f"Bulk-deleted {affected} customers ({len(payload.ids)} requested)",
        user=current_user, request=request, db=db,
    )
    return {"deleted": affected}


@router.get("/stats/summary")
async def customers_summary(db: AsyncSession = Depends(get_db)):
    """Aggregate customer statistics (total, active, by type, by status)."""
    total = (
        await db.execute(
            select(func.count(Customer.id)).where(Customer.is_deleted == False)
        )
    ).scalar() or 0
    active = (
        await db.execute(
            select(func.count(Customer.id)).where(
                and_(Customer.is_deleted == False, Customer.status == "active")
            )
        )
    ).scalar() or 0

    by_type = {}
    for t in AccountType:
        count = (
            await db.execute(
                select(func.count(Customer.id)).where(
                    and_(Customer.is_deleted == False, Customer.account_type == t)
                )
            )
        ).scalar() or 0
        by_type[t.value] = count

    by_status = {}
    for s in CustomerStatus:
        count = (
            await db.execute(
                select(func.count(Customer.id)).where(
                    and_(Customer.is_deleted == False, Customer.status == s)
                )
            )
        ).scalar() or 0
        by_status[s.value] = count

    return {"total": total, "active": active, "by_type": by_type, "by_status": by_status}


@router.get("/{customer_id}/facilities")
async def get_customer_facilities(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Return a customer together with its (non-deleted) facilities."""
    customer = await _get_active_customer(customer_id, db)
    result = await db.execute(
        select(Facility).where(
            Facility.customer_id == customer_id, Facility.is_deleted == False
        )
    )
    facilities = result.scalars().all()
    return {
        "customer": CustomerResponse.model_validate(customer),
        "facilities": [FacilityResponse.model_validate(f) for f in facilities],
        "total_facilities": len(facilities),
    }


@router.get("/{customer_id}/detail")
async def get_customer_detail(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Full customer profile: facilities, offer letters and a financial summary."""
    customer = await _get_active_customer(customer_id, db)

    facilities = (
        await db.execute(
            select(Facility).where(
                Facility.customer_id == customer_id, Facility.is_deleted == False
            )
        )
    ).scalars().all()

    offers = (
        await db.execute(
            select(OfferLetter).where(
                OfferLetter.customer_id == customer_id, OfferLetter.is_deleted == False
            )
        )
    ).scalars().all()

    # ---- Connected CRM data (merged from the legacy system), keyed by account_no ----
    import json as _json
    from sqlalchemy import inspect as _sa_inspect
    from app.models.guarantor import Guarantor
    from app.models.crm import (
        CustomerProfile, ChecklistProgress, CustomTask, Attachment, JournalEntry,
    )

    def _to_dict(obj):
        return {c.key: getattr(obj, c.key) for c in _sa_inspect(obj).mapper.column_attrs}

    acc = customer.account_no

    async def _by_acc(model, order=None, limit=None):
        q = select(model).where(model.account_no == acc)
        if hasattr(model, "is_deleted"):
            q = q.where(model.is_deleted == False)
        if order is not None:
            q = q.order_by(order)
        if limit:
            q = q.limit(limit)
        return (await db.execute(q)).scalars().all()

    guarantors = await _by_acc(Guarantor)
    tasks = await _by_acc(CustomTask)
    attachments = await _by_acc(Attachment)
    journal = await _by_acc(JournalEntry, order=JournalEntry.date.desc(), limit=60)
    profile_row = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
    ).scalar_one_or_none()
    checklist_row = (
        await db.execute(select(ChecklistProgress).where(ChecklistProgress.account_no == acc))
    ).scalar_one_or_none()

    profile = None
    if profile_row is not None:
        profile = _to_dict(profile_row)
        try:
            profile["data"] = _json.loads(profile_row.data_json or "{}")
        except Exception:
            profile["data"] = {}
        profile.pop("data_json", None)

    total_exposure = sum(float(f.amount or 0) for f in facilities)
    total_outstanding = sum(float(f.outstanding or 0) for f in facilities)
    active_facilities = sum(
        1 for f in facilities
        if getattr(f.status, "value", f.status) == "active"
    )

    return {
        "customer": CustomerResponse.model_validate(customer),
        "facilities": [FacilityResponse.model_validate(f) for f in facilities],
        "offer_letters": [OfferLetterResponse.model_validate(o) for o in offers],
        "guarantors": [_to_dict(g) for g in guarantors],
        "tasks": [_to_dict(t) for t in tasks],
        "attachments": [_to_dict(a) for a in attachments],
        "journal": [_to_dict(j) for j in journal],
        "profile": profile,
        "checklist": _to_dict(checklist_row) if checklist_row is not None else None,
        "summary": {
            "total_facilities": len(facilities),
            "active_facilities": active_facilities,
            "total_offers": len(offers),
            "total_guarantors": len(guarantors),
            "total_exposure": total_exposure,
            "total_outstanding": total_outstanding,
            "currency": "AED",
        },
    }


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific customer by ID."""
    return await _get_active_customer(customer_id, db)


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Create a new customer (account number must be unique)."""
    if customer_data.account_no:
        existing = await db.execute(
            select(Customer).where(Customer.account_no == customer_data.account_no)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this account number already exists",
            )

    customer = Customer(**customer_data.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    await record_audit(
        action="create", entity_type="customer", entity_id=customer.id,
        detail=f"Created customer '{customer.name}'", user=current_user, request=request, db=db,
    )
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Update an existing customer."""
    customer = await _get_active_customer(customer_id, db)

    update_data = customer_data.model_dump(exclude_unset=True)
    new_account_no = update_data.get("account_no")
    if new_account_no and new_account_no != customer.account_no:
        existing = await db.execute(
            select(Customer).where(
                Customer.account_no == new_account_no, Customer.id != customer_id
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another customer with this account number already exists",
            )

    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)
    await record_audit(
        action="update", entity_type="customer", entity_id=customer.id,
        detail=f"Updated customer '{customer.name}'", user=current_user, request=request, db=db,
    )
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_editor),
):
    """Soft delete a customer."""
    customer = await _get_active_customer(customer_id, db)
    customer.is_deleted = True
    await db.commit()
    await record_audit(
        action="delete", entity_type="customer", entity_id=customer.id,
        detail=f"Deleted customer '{customer.name}'", user=current_user, request=request, db=db,
    )
    return None


@router.post("/{customer_id}/restore", response_model=CustomerResponse)
async def restore_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Restore a soft-deleted customer and re-activate it."""
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id, Customer.is_deleted == True
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_CUSTOMER_NOT_FOUND
        )

    customer.is_deleted = False
    customer.status = CustomerStatus.ACTIVE
    await db.commit()
    await db.refresh(customer)
    return customer
