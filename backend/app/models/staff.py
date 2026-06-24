"""Staff directory — bank employees with their department, contact details and an
editable Persian name.

People move between departments or leave often, so every field is editable from
the UI. ``region`` separates the UAE (Persian Gulf) list from any Iran-side list
added later. ``name_fa`` lets a user reuse the correct Persian spelling of a name
without re-typing it (and risking a typo).
"""
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


def generate_staff_id() -> str:
    return uuid.uuid4().hex


class StaffMember(Base):
    __tablename__ = "staff_members"

    id = Column(String(32), primary_key=True, default=generate_staff_id)
    name = Column(String(200), nullable=False, index=True)   # English name (as in the source)
    name_fa = Column(String(200))                            # Persian equivalent (editable)
    department = Column(String(200), index=True)
    title = Column(String(150))                              # role / position (editable)
    telephone = Column(String(60))
    ext = Column(String(20))
    fax = Column(String(60))
    email = Column(String(150), index=True)
    mobile = Column(String(60))
    region = Column(String(80), default="Persian Gulf", index=True)  # Persian Gulf | Iran | …
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String(80))

    def __init__(self, **kwargs):
        kwargs.setdefault("region", "Persian Gulf")
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<StaffMember(name='{self.name}', dept='{self.department}')>"
