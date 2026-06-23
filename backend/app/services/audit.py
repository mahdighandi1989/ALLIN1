"""Best-effort audit logging.

``record_audit`` writes one AuditLog row using its OWN short-lived session, so it
is independent of the caller's transaction and a failure here never affects (or
rolls back) the request that triggered it.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request

from app.database import AsyncSessionLocal
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def _client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


async def record_audit(
    *,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    account_no: Optional[str] = None,
    detail: Optional[str] = None,
    user=None,
    request: Optional[Request] = None,
    db=None,
) -> None:
    """Persist a single audit entry (never raises).

    ``account_no`` ties the action to a customer so it appears under that
    customer's profile (and is linkable from the global log).

    If ``db`` (the caller's session) is supplied the entry is written through it,
    so the trail honours the same engine/override as the request — this is what
    lets tests (which override get_db) see the entry. Otherwise a private
    short-lived session keeps production audit writes independent of the caller.
    """
    entry = AuditLog(
        user_id=str(getattr(user, "id", "")) or None,
        username=getattr(user, "username", None),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        account_no=(str(account_no).strip() or None) if account_no is not None else None,
        detail=detail,
        ip_address=_client_ip(request),
    )
    try:
        if db is not None:
            db.add(entry)
            await db.commit()
        else:
            async with AsyncSessionLocal() as session:
                session.add(entry)
                await session.commit()
    except Exception as exc:  # pragma: no cover - logging must never break a request
        logger.warning("Audit log write failed (%s %s): %s", action, entity_type, exc)
