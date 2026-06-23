"""Activity / audit log. Wired at /api/audit.

Three surfaces over one append-only ``AuditLog`` table:

* ``GET /``                     — the global log (admin-only).
* ``GET /customer/{account_no}``— that customer's log, for the profile «Logs» tab
                                  (any authenticated user who can see the profile).
* ``POST /activity``            — lets the SPA record a client-side action
                                  (e.g. a printed voucher / official letter).

Every entry is enriched with the related customer's id + name (resolved from
``account_no``) so both the profile tab and the global page can deep-link.
"""
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.routers.auth import require_admin, get_current_active_user
from app.services.audit import record_audit

router = APIRouter(tags=["audit"])


class AuditEntry(BaseModel):
    id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    account_no: Optional[str] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None
    # Resolved from account_no so the UI can deep-link to the customer profile.
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditListResponse(BaseModel):
    items: List[AuditEntry]
    total: int
    page: int
    page_size: int


async def _to_entries(db: AsyncSession, rows) -> List[AuditEntry]:
    """Map ORM rows to AuditEntry, attaching customer id/name for each account_no
    in one extra query (so links work without an N+1)."""
    entries = [AuditEntry.model_validate(r) for r in rows]
    accounts = {e.account_no for e in entries if e.account_no}
    if accounts:
        cust = (
            await db.execute(
                select(Customer.account_no, Customer.id, Customer.name).where(
                    Customer.account_no.in_(accounts)
                )
            )
        ).all()
        by_acc: Dict[str, tuple] = {c.account_no: (c.id, c.name) for c in cust}
        for e in entries:
            if e.account_no and e.account_no in by_acc:
                e.customer_id, e.customer_name = by_acc[e.account_no]
    return entries


def _apply_filters(base, *, action, entity_type, account_no, search):
    if action:
        base = base.where(AuditLog.action == action)
    if entity_type:
        base = base.where(AuditLog.entity_type == entity_type)
    if account_no:
        base = base.where(AuditLog.account_no == account_no)
    if search:
        like = f"%{search}%"
        base = base.where(
            or_(
                AuditLog.username.ilike(like),
                AuditLog.detail.ilike(like),
                AuditLog.entity_id.ilike(like),
                AuditLog.account_no.ilike(like),
                AuditLog.entity_type.ilike(like),
                AuditLog.action.ilike(like),
            )
        )
    return base


async def _paged(db, base, page, page_size) -> AuditListResponse:
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar() or 0
    rows = (
        await db.execute(
            base.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return AuditListResponse(
        items=await _to_entries(db, rows), total=total, page=page, page_size=page_size
    )


@router.get("/", response_model=AuditListResponse, dependencies=[Depends(require_admin)])
async def list_audit(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    account_no: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search user / detail / account / entity / action"),
):
    """The whole-program activity log (admin only)."""
    base = _apply_filters(
        select(AuditLog), action=action, entity_type=entity_type,
        account_no=account_no, search=search,
    )
    return await _paged(db, base, page, page_size)


@router.get(
    "/customer/{account_no}",
    response_model=AuditListResponse,
    dependencies=[Depends(get_current_active_user)],
)
async def list_customer_audit(
    account_no: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    action: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """Everything that happened to one customer — powers the profile «Logs» tab."""
    base = _apply_filters(
        select(AuditLog).where(AuditLog.account_no == account_no),
        action=action, entity_type=None, account_no=None, search=search,
    )
    return await _paged(db, base, page, page_size)


class ActivityIn(BaseModel):
    action: str = Field(min_length=1, max_length=50)
    entity_type: Optional[str] = Field(default=None, max_length=50)
    entity_id: Optional[str] = Field(default=None, max_length=64)
    account_no: Optional[str] = Field(default=None, max_length=50)
    detail: Optional[str] = Field(default=None, max_length=1000)


@router.post("/activity", dependencies=[Depends(get_current_active_user)])
async def log_activity(
    payload: ActivityIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_active_user),
):
    """Record an action performed in the SPA (printed forms, generated letters, …)
    so it shows up under the customer's profile and in the global log."""
    await record_audit(
        action=payload.action,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        account_no=payload.account_no,
        detail=payload.detail,
        user=user,
        request=request,
        db=db,
    )
    return {"status": "logged"}
