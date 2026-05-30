"""Audit-log viewing (admin-only). Wired at /api/audit."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

from app.database import get_db
from app.models.audit_log import AuditLog
from app.routers.auth import require_admin

router = APIRouter(tags=["audit"], dependencies=[Depends(require_admin)])


class AuditEntry(BaseModel):
    id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuditListResponse(BaseModel):
    items: List[AuditEntry]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=AuditListResponse)
async def list_audit(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search username / detail / entity id"),
):
    base = select(AuditLog)
    if action:
        base = base.where(AuditLog.action == action)
    if entity_type:
        base = base.where(AuditLog.entity_type == entity_type)
    if search:
        like = f"%{search}%"
        base = base.where(
            or_(
                AuditLog.username.ilike(like),
                AuditLog.detail.ilike(like),
                AuditLog.entity_id.ilike(like),
            )
        )

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
    return AuditListResponse(items=rows, total=total, page=page, page_size=page_size)
