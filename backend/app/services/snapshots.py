"""Monthly exposure snapshot capture + backfill.

``capture_current_snapshot`` upserts a row for the current month from live data.
``backfill_demo_history`` seeds a few months of plausible history the first time
so the dashboard trend has a real series to draw. Both are best-effort.
"""
from __future__ import annotations

import logging
from datetime import date

import sqlalchemy as sa

from app.database import AsyncSessionLocal
from app.models.exposure_snapshot import ExposureSnapshot
from app.models.facility import Facility
from app.models.customer import Customer

logger = logging.getLogger(__name__)


async def _current_totals(session) -> dict:
    exposure = float(
        (
            await session.execute(
                sa.select(sa.func.coalesce(sa.func.sum(sa.cast(Facility.amount, sa.Float)), 0.0))
                .where(Facility.is_deleted == False)
            )
        ).scalar()
        or 0
    )
    outstanding = float(
        (
            await session.execute(
                sa.select(sa.func.coalesce(sa.func.sum(sa.cast(Facility.outstanding, sa.Float)), 0.0))
                .where(Facility.is_deleted == False)
            )
        ).scalar()
        or 0
    )
    fac_count = (
        await session.execute(
            sa.select(sa.func.count(Facility.id)).where(Facility.is_deleted == False)
        )
    ).scalar() or 0
    cust_count = (
        await session.execute(
            sa.select(sa.func.count(Customer.id)).where(Customer.is_deleted == False)
        )
    ).scalar() or 0
    return {
        "total_exposure": exposure,
        "total_outstanding": outstanding,
        "facility_count": int(fac_count),
        "customer_count": int(cust_count),
    }


async def _upsert(session, year: int, month: int, totals: dict) -> None:
    existing = (
        await session.execute(
            sa.select(ExposureSnapshot).where(
                ExposureSnapshot.year == year, ExposureSnapshot.month == month
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.total_exposure = totals["total_exposure"]
        existing.total_outstanding = totals["total_outstanding"]
        existing.facility_count = totals["facility_count"]
        existing.customer_count = totals["customer_count"]
    else:
        session.add(ExposureSnapshot(year=year, month=month, **totals))


async def capture_current_snapshot() -> None:
    """Upsert this month's snapshot from current data (idempotent)."""
    try:
        async with AsyncSessionLocal() as session:
            totals = await _current_totals(session)
            today = date.today()
            await _upsert(session, today.year, today.month, totals)
            await session.commit()
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.error("Snapshot capture skipped: %s", exc)


async def backfill_demo_history(months: int = 6) -> None:
    """Seed prior months with a plausible ramp up to current totals (once).

    Skips entirely if any snapshot already exists, so it never overwrites real
    captured history.
    """
    try:
        async with AsyncSessionLocal() as session:
            count = (
                await session.execute(sa.select(sa.func.count(ExposureSnapshot.id)))
            ).scalar() or 0
            if count:
                return
            totals = await _current_totals(session)
            if totals["total_exposure"] <= 0:
                return

            today = date.today()
            # Build (months) buckets ending at the current month.
            buckets = []
            y, m = today.year, today.month
            for _ in range(months):
                buckets.append((y, m))
                m -= 1
                if m == 0:
                    m, y = 12, y - 1
            buckets.reverse()

            n = len(buckets)
            for i, (by, bm) in enumerate(buckets):
                # Linear ramp from ~55% to 100% of current totals.
                factor = 0.55 + 0.45 * (i / max(1, n - 1))
                await _upsert(
                    session, by, bm,
                    {
                        "total_exposure": round(totals["total_exposure"] * factor, 2),
                        "total_outstanding": round(totals["total_outstanding"] * factor, 2),
                        "facility_count": max(1, int(totals["facility_count"] * factor)),
                        "customer_count": max(1, int(totals["customer_count"] * factor)),
                    },
                )
            await session.commit()
            logger.info("Backfilled %s months of exposure snapshots", n)
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.error("Snapshot backfill skipped: %s", exc)
