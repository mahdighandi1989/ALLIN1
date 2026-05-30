"""Tests for the exposure snapshot time series feeding the dashboard trend."""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.exposure_snapshot import ExposureSnapshot
from app.services.snapshots import capture_current_snapshot, backfill_demo_history
import app.services.snapshots as snapshots_mod
import app.database as database


@pytest.fixture
def _use_test_session(db_session, monkeypatch):
    """Point the snapshot service's own-session factory at the test session."""
    class _Maker:
        def __call__(self):
            class _Ctx:
                async def __aenter__(self_inner):
                    return db_session
                async def __aexit__(self_inner, *a):
                    return False
            return _Ctx()
    monkeypatch.setattr(snapshots_mod, "AsyncSessionLocal", _Maker())
    return db_session


class TestSnapshots:
    async def test_capture_upserts_current_month(self, _use_test_session, db_session):
        c = Customer(account_no="SNAP-1", name="Snap Co")
        db_session.add(c)
        await db_session.flush()
        db_session.add(Facility(customer_id=c.id, facility_type=FacilityType.LOAN,
                                amount=Decimal("1000000"), outstanding=Decimal("400000"),
                                status=FacilityStatus.ACTIVE))
        await db_session.commit()

        await capture_current_snapshot()
        snaps = (await db_session.execute(ExposureSnapshot.__table__.select())).all()
        assert len(snaps) == 1

        # Capturing again is idempotent (still one row, updated value).
        await capture_current_snapshot()
        snaps2 = (await db_session.execute(ExposureSnapshot.__table__.select())).all()
        assert len(snaps2) == 1

    async def test_backfill_creates_history_then_noops(self, _use_test_session, db_session):
        c = Customer(account_no="SNAP-2", name="Hist Co")
        db_session.add(c)
        await db_session.flush()
        db_session.add(Facility(customer_id=c.id, facility_type=FacilityType.LOAN,
                                amount=Decimal("5000000"), status=FacilityStatus.ACTIVE))
        await db_session.commit()

        await backfill_demo_history(months=6)
        rows = (await db_session.execute(ExposureSnapshot.__table__.select())).all()
        assert len(rows) == 6

        # Second backfill is a no-op (history already exists).
        await backfill_demo_history(months=6)
        rows2 = (await db_session.execute(ExposureSnapshot.__table__.select())).all()
        assert len(rows2) == 6

    async def test_dashboard_trend_uses_snapshots(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        # Seed three explicit monthly snapshots.
        db_session.add_all([
            ExposureSnapshot(year=2026, month=3, total_exposure=Decimal("100"), facility_count=2, customer_count=1),
            ExposureSnapshot(year=2026, month=4, total_exposure=Decimal("200"), facility_count=4, customer_count=2),
            ExposureSnapshot(year=2026, month=5, total_exposure=Decimal("300"), facility_count=6, customer_count=3),
        ])
        await db_session.commit()

        data = (await client.get("/api/stats/dashboard", headers=auth_headers)).json()
        trend = data["monthly_trend"]
        # Uses the snapshot series (ascending), not the live-cumulative fallback.
        assert [p["month"] for p in trend[-3:]] == ["2026-03", "2026-04", "2026-05"]
        assert [p["exposure"] for p in trend[-3:]] == [100.0, 200.0, 300.0]
        assert trend[-1]["facilities"] == 6

    async def test_snapshot_endpoint(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/stats/snapshot", headers=auth_headers)
        assert r.status_code == 200 and r.json()["ok"] is True

    async def test_snapshot_requires_auth(self, client: AsyncClient):
        assert (await client.post("/api/stats/snapshot")).status_code == 401
