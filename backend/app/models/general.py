"""General (non-account) profiles, each with multiple checklists and items.

The Excel system let the user keep profiles for recurring topics that are NOT a
specific customer account (ShowGeneralProfilesList / GeneralChecklists), each
with several checklists and tickable items (requirement A7). These three tables
are that feature: a GeneralProfile has many GeneralChecklists, each of which has
many GeneralChecklistItems.
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class GeneralProfile(Base):
    __tablename__ = "general_profiles"

    id = Column(String(40), primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(60))
    created_by = Column(String(80))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GeneralChecklist(Base):
    __tablename__ = "general_checklists"

    id = Column(String(40), primary_key=True)
    profile_id = Column(String(40), index=True, nullable=False)
    title = Column(String(200), nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GeneralChecklistItem(Base):
    __tablename__ = "general_checklist_items"

    id = Column(String(40), primary_key=True)
    checklist_id = Column(String(40), index=True, nullable=False)
    text = Column(Text, nullable=False)
    is_done = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
