"""History of database-cleanup runs (scan reports + applied removals)."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


def _gen_id() -> str:
    return "CLR" + uuid.uuid4().hex[:16]


class CleanupRun(Base):
    __tablename__ = "cleanup_runs"

    id = Column(String(24), primary_key=True, default=_gen_id)
    kind = Column(String(20), nullable=False, default="scan")       # scan | apply | scheduled
    trigger = Column(String(20), nullable=False, default="manual")  # manual | schedule
    username = Column(String(120))
    counts_json = Column(Text)   # JSON summary (per-entity counts, total_removals, …)
    detail = Column(Text)        # short human note
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CleanupRun {self.id} {self.kind} {self.created_at}>"
