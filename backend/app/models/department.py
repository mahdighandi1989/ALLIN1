"""Recipient departments (ادارات) + their managers — the address book the official
letter's «گیرنده» fields draw from.

Each department keeps its CURRENT manager plus an ordered history of PREVIOUS
managers (managers change over time). Names are matched by a normalized key so a
small spelling difference doesn't create a duplicate department.
"""
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


def generate_dept_id() -> str:
    return uuid.uuid4().hex


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(32), primary_key=True, default=generate_dept_id)
    name = Column(String(200), nullable=False, index=True)   # primary name (usually Persian)
    name_fa = Column(String(200))                            # alternate / Persian spelling
    name_norm = Column(String(200), index=True)              # normalized key for dedup
    current_manager = Column(String(200))
    current_manager_fa = Column(String(200))
    manager_title = Column(String(120))                      # e.g. «رئیس محترم»
    # Ordered JSON list of replaced managers (oldest → most-recent-previous):
    #   [{"name": "...", "name_fa": "...", "until": "YYYY-MM-DD"}]
    previous_managers = Column(Text)
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String(80))

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Department(name='{self.name}', manager='{self.current_manager}')>"
