"""In-app notification model — per-user messages shown in the UI bell.

Notifications are lightweight rows scoped to a user (or broadcast when
``user_id`` is NULL). Written best-effort by ``app.services.notify_inapp`` so a
failure never breaks the triggering request.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from app.database import Base


def generate_notification_id() -> str:
    return uuid.uuid4().hex


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(32), primary_key=True, default=generate_notification_id)
    # Recipient. NULL = broadcast (visible to everyone).
    user_id = Column(String(33), index=True)
    level = Column(String(20), default="info")   # info / success / warning / error
    title = Column(String(200), nullable=False)
    message = Column(Text)
    # Optional deep link the UI can navigate to (e.g. "/facilities").
    link = Column(String(255))
    category = Column(String(50), index=True)    # e.g. facility/offer_letter/system
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return (
            f"<Notification(id='{self.id}', user='{self.user_id}', "
            f"level='{self.level}', read={self.is_read})>"
        )


class NotificationRead(Base):
    """Per-user read marker for BROADCAST notifications (user_id IS NULL).

    Broadcast rows are shared, so their ``is_read`` flag cannot carry per-user
    state — before this table existed, the first user to click "mark read"
    hid the notification from everyone else's bell. Personal notifications
    keep using ``Notification.is_read``; a broadcast with ``is_read=True`` is
    treated as read-for-all (legacy rows marked before this table existed).
    """

    __tablename__ = "notification_reads"

    notification_id = Column(
        String(32), ForeignKey("notifications.id"), primary_key=True
    )
    user_id = Column(String(33), primary_key=True)
    read_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<NotificationRead(note='{self.notification_id}', user='{self.user_id}')>"
