"""Monthly exposure snapshots — a real time series of portfolio totals.

One row per (year, month) capturing the book's totals at snapshot time, so the
dashboard trend reflects actual recorded history instead of being recomputed from
current rows. Snapshots are upserted (idempotent per month) at startup.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, Numeric, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


def generate_snapshot_id() -> str:
    return uuid.uuid4().hex


class ExposureSnapshot(Base):
    __tablename__ = "exposure_snapshots"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_exposure_year_month"),)

    id = Column(String(32), primary_key=True, default=generate_snapshot_id)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12
    total_exposure = Column(Numeric(18, 2), default=0)
    total_outstanding = Column(Numeric(18, 2), default=0)
    facility_count = Column(Integer, default=0)
    customer_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def label(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def __repr__(self) -> str:
        return f"<ExposureSnapshot({self.label}, exposure={self.total_exposure})>"
