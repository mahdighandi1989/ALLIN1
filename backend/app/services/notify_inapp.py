"""Best-effort in-app notification creation.

Mirrors the audit service: ``create_notification`` writes one row using the
caller's session when provided (so it honours test overrides) or its own
short-lived session otherwise, and never raises.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.database import AsyncSessionLocal
from app.models.notification import Notification

logger = logging.getLogger(__name__)


async def create_notification(
    *,
    title: str,
    message: Optional[str] = None,
    user_id: Optional[str] = None,
    level: str = "info",
    link: Optional[str] = None,
    category: Optional[str] = None,
    db=None,
) -> None:
    """Create one notification (never raises). user_id=None => broadcast."""
    note = Notification(
        user_id=user_id,
        level=level,
        title=title,
        message=message,
        link=link,
        category=category,
        is_read=False,
    )
    try:
        if db is not None:
            db.add(note)
            await db.commit()
        else:
            async with AsyncSessionLocal() as session:
                session.add(note)
                await session.commit()
    except Exception as exc:  # pragma: no cover - must never break a request
        logger.warning("In-app notification write failed (%s): %s", title, exc)
