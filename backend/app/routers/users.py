"""Admin user management (admin-only). Wired at /api/users."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.admin_user import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserListResponse,
)
from app.routers.auth import require_admin, get_current_active_user
from app.utils.security import hash_password
from app.services.audit import record_audit

logger = logging.getLogger(__name__)

# Every endpoint requires an authenticated admin.
router = APIRouter(tags=["users"], dependencies=[Depends(require_admin)])

_NOT_FOUND = "User not found"


async def _get_user(user_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return user


@router.get("/", response_model=AdminUserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search username / email / full name"),
):
    base = select(User)
    if search:
        like = f"%{search}%"
        base = base.where(
            or_(
                User.username.ilike(like),
                User.email.ilike(like),
                User.full_name.ilike(like),
            )
        )
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar() or 0
    rows = (
        await db.execute(
            base.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    # Serialise each row individually so a single legacy/corrupt row can never
    # 500 the whole list. AdminUserResponse already coerces NULLs in
    # role/auth_provider/is_active/is_admin; this is the belt-and-braces guard
    # for anything else that slips through — the endpoint must stay a 200.
    items = []
    for row in rows:
        try:
            items.append(AdminUserResponse.model_validate(row))
        except Exception as exc:  # pragma: no cover - defensive, depends on dirty data
            logger.warning("list_users: skipping unserialisable user row id=%s: %s",
                           getattr(row, "id", "?"), exc)
    return AdminUserListResponse(items=items, total=total, page=page, page_size=page_size)


# Admin single-user fetch: a valid REST member of the admin users resource that
# the SPA does not currently consume (it lists/creates/updates/deactivates via
# the sibling routes). Kept for API/admin completeness but hidden from the public
# OpenAPI schema (unused-endpoint audit, see docs/ENDPOINT_AUDIT.md).
@router.get("/{user_id}", response_model=AdminUserResponse, include_in_schema=False)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    return await _get_user(user_id, db)


@router.post("/", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_active_user),
):
    username = payload.username.lower()
    email = payload.email.lower()

    if (await db.execute(select(User).where(User.username == username))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Honour an explicit access level when given; otherwise an admin-created
    # account is trusted and defaults to 'admin' (if is_admin) or 'editor' — never
    # the 'pending' approval state used for self-service Google sign-ups. role and
    # is_admin are kept in sync so the two never disagree.
    role = payload.role or ("admin" if payload.is_admin else "editor")
    is_admin = payload.is_admin or role == "admin"
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=payload.is_active,
        is_admin=is_admin,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await record_audit(
        action="create", entity_type="user", entity_id=user.id,
        detail=f"Created user '{user.username}' (admin={user.is_admin})",
        user=actor, request=request, db=db,
    )
    return user


@router.put("/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_active_user),
):
    user = await _get_user(user_id, db)
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"]:
        new_email = data["email"].lower()
        existing = (
            await db.execute(
                select(User).where(User.email == new_email, User.id != user_id)
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = new_email

    if data.get("password"):
        user.hashed_password = hash_password(data["password"])
    if "full_name" in data and data["full_name"] is not None:
        user.full_name = data["full_name"]
    if "is_active" in data and data["is_active"] is not None:
        user.is_active = data["is_active"]
    # role and is_admin are kept in sync: granting 'admin' sets is_admin, and a
    # legacy is_admin toggle maps onto the role.
    if "role" in data and data["role"]:
        user.role = data["role"]
        user.is_admin = data["role"] == "admin"
    if "is_admin" in data and data["is_admin"] is not None:
        user.is_admin = data["is_admin"]
        if data["is_admin"] and user.role != "admin":
            user.role = "admin"
        elif not data["is_admin"] and user.role == "admin":
            user.role = "editor"  # demoted admins keep edit access, not pending

    await db.commit()
    await db.refresh(user)
    await record_audit(
        action="update", entity_type="user", entity_id=user.id,
        detail=f"Updated user '{user.username}'", user=actor, request=request, db=db,
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deactivate a user (kept as a soft action — never hard-deletes the row).

    Guards against an admin locking everyone out by refusing to deactivate the
    last remaining active admin, and refuses self-deactivation.
    """
    user = await _get_user(user_id, db)

    if current_user is not None and getattr(current_user, "id", None) == user.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

    if user.is_admin and user.is_active:
        active_admins = (
            await db.execute(
                select(func.count(User.id)).where(
                    User.is_admin == True, User.is_active == True
                )
            )
        ).scalar() or 0
        if active_admins <= 1:
            raise HTTPException(
                status_code=400, detail="Cannot deactivate the last active admin"
            )

    user.is_active = False
    await db.commit()
    await record_audit(
        action="delete", entity_type="user", entity_id=user.id,
        detail=f"Deactivated user '{user.username}'", user=current_user, request=request, db=db,
    )
    return None
