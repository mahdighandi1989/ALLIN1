"""Saved official letters (نامه‌ها).

A letter is stored either UNDER a customer account (``account_no`` set → shown in
that profile's «نامه‌ها» tab) or as a GENERAL letter (no account → shown in a shared
«نامه‌های عمومی» bucket). Each row keeps the form values AND a per-letter layout so
edits to fields/positions belong to that letter, never the master template.
"""
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


def generate_letter_id() -> str:
    return uuid.uuid4().hex


class Letter(Base):
    __tablename__ = "letters"

    id = Column(String(32), primary_key=True, default=generate_letter_id)
    account_no = Column(String(50), index=True)        # blank/None → general letter
    category = Column(String(20), default="account", index=True)  # account | general
    title = Column(String(255))
    subject = Column(String(500))
    recipient_dept = Column(String(200))
    recipient_manager = Column(String(200))
    values_json = Column(Text)   # the letter form values (f)
    layout_json = Column(Text)   # per-letter field layout overrides (L)
    labels_json = Column(Text)   # per-letter label overrides
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(80))
    updated_by = Column(String(80))

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Letter(id='{self.id}', account='{self.account_no or 'general'}', title='{self.title}')>"
