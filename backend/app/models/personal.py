"""Private, per-user personal notes (the Excel personal-notes panel, A8/A11).

Scoped to the owning user by ``username`` and surfaced only through the
user-scoped /api/personal endpoints, so they stay private (the Excel version
deliberately kept them out of the shared backend folder). Each note is
checklist-like (``is_done``) and tracks whether it has been emailed
(``is_sent``) for the one-button email digest (A16).
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class PersonalNote(Base):
    __tablename__ = "personal_notes"

    id = Column(String(50), primary_key=True)
    username = Column(String(80), index=True, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(60))
    is_done = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    created_date = Column(String(30))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
