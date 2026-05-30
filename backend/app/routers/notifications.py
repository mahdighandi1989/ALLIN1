"""In-app notifications for the current user (bell menu)."""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(tags=["notifications"], dependencies=[Depends(get_current_user)])


class NotificationResponse(BaseModel):
    id: str
    level: str
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    category: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread: int
    page: int = 1
    page_size: int = 50


def _visible_to(user: User):
    """Rows for this user OR broadcasts (user_id IS NULL)."""
    uid = str(getattr(user, "id", "")) or None
    return or_(Notification.user_id == uid, Notification.user_id.is_(None))


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
):
    cond = _visible_to(current_user)
    base = select(Notification).where(cond)
    if unread_only:
        base = base.where(Notification.is_read == False)

    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar() or 0
    unread = (
        await db.execute(
            select(func.count()).select_from(
                select(Notification)
                .where(cond, Notification.is_read == False)
                .subquery()
            )
        )
    ).scalar() or 0

    rows = (
        await db.execute(
            base.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return NotificationListResponse(
        items=rows, total=total, unread=unread, page=page, page_size=page_size
    )


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    n = (
        await db.execute(
            select(func.count()).select_from(
                select(Notification)
                .where(_visible_to(current_user), Notification.is_read == False)
                .subquery()
            )
        )
    ).scalar() or 0
    return {"unread": n}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, _visible_to(current_user)
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    note.is_read = True
    await db.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification)
        .where(_visible_to(current_user), Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"ok": True}
