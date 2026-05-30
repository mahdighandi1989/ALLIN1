"""Audit log model — an append-only trail of notable actions.

Records who did what to which entity and when. Written best-effort by
``app.services.audit.record_audit`` so a logging failure never breaks the
underlying request.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


def generate_audit_id() -> str:
    return uuid.uuid4().hex


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(32), primary_key=True, default=generate_audit_id)
    # Actor.
    user_id = Column(String(33), index=True)
    username = Column(String(50), index=True)
    # What happened.
    action = Column(String(50), nullable=False, index=True)   # e.g. create/update/delete/login
    entity_type = Column(String(50), index=True)              # customer/facility/offer_letter/user/auth
    entity_id = Column(String(64), index=True)
    detail = Column(Text)
    ip_address = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id='{self.id}', action='{self.action}', "
            f"entity='{self.entity_type}:{self.entity_id}', user='{self.username}')>"
        )
