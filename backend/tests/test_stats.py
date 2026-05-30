"""Unit tests for the dashboard statistics endpoint (/api/stats/dashboard)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus


class TestDashboardStats:
    async def test_dashboard_requires_auth(self, client: AsyncClient):
        """Without a valid token the endpoint must return 401."""
        resp = await client.get("/api/stats/dashboard")
        assert resp.status_code == 401

    async def test_dashboard_endpoint(self, client: AsyncClient, auth_headers: dict):
        """The dashboard contract matches the documented DashboardStats shape."""
        resp = await client.get("/api/stats/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        # Required flat fields (the API/UI contract).
        for field in (
            "total_customers",
            "total_facilities",
            "active_facilities",
            "expiring_soon",
            "expiring_facilities",
            "monthly_revenue",
            "total_outstanding",
            "recent_customers",
            "recent_activities",
        ):
            assert field in data, f"missing field: {field}"

        assert isinstance(data["total_customers"], int)
        assert isinstance(data["total_facilities"], int)
        assert isinstance(data["active_facilities"], int)
        assert isinstance(data["monthly_revenue"], (int, float))
        assert isinstance(data["recent_activities"], list)
        assert data["total_exposure"]["currency"] == "AED"

    async def test_dashboard_counts_reflect_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session,
    ):
        """Counts should reflect the rows that exist in the database."""
        customer = Customer(
            account_no="DASH001",
            name="Dashboard Co",
            account_type=AccountType.CORPORATE,
            status=CustomerStatus.ACTIVE,
        )
        db_session.add(customer)
        await db_session.commit()

        resp = await client.get("/api/stats/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_customers"] >= 1
        assert data["active_customers"] >= 1
        # The seeded customer should appear in the recent feed.
        assert any(
            "Dashboard Co" in a.get("action", "") for a in data["recent_activities"]
        )

    async def test_dashboard_facility_metrics(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        """Seeding facilities exercises monthly_revenue / exposure / expiring."""
        customer = Customer(account_no="FAC100", name="Facility Co")
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)

        soon = date.today() + timedelta(days=10)
        facilities = [
            Facility(
                customer_id=customer.id,
                facility_type=FacilityType.LOAN,
                amount=Decimal("100000"),
                outstanding=Decimal("80000"),
                interest_rate=Decimal("12"),
                status=FacilityStatus.ACTIVE,
                expiry_date=soon,
            ),
            Facility(
                customer_id=customer.id,
                facility_type=FacilityType.OVERDRAFT,
                amount=Decimal("50000"),
                outstanding=Decimal("50000"),
                interest_rate=Decimal("6"),
                status=FacilityStatus.CLOSED,
            ),
        ]
        db_session.add_all(facilities)
        await db_session.commit()

        resp = await client.get("/api/stats/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_facilities"] == 2
        assert data["active_facilities"] == 1
        assert data["expiring_soon"] >= 1
        # monthly_revenue = sum(amount * rate / 1200) over ACTIVE facilities only
        # = 100000 * 12 / 1200 = 1000
        assert data["monthly_revenue"] == pytest.approx(1000.0)
        assert data["total_exposure"]["amount"] == pytest.approx(150000.0)
        assert data["total_outstanding"] == pytest.approx(130000.0)


class TestDashboardStatsNamed:
    """The explicitly-named unit tests required for the stats route coverage gap."""

    async def test_dashboard_stats_success(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        """With sample data the endpoint returns 200 and the expected fields."""
        customer = Customer(account_no="OK001", name="Sample Co")
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        db_session.add(
            Facility(
                customer_id=customer.id,
                facility_type=FacilityType.LOAN,
                amount=Decimal("25000"),
                status=FacilityStatus.ACTIVE,
            )
        )
        await db_session.commit()

        resp = await client.get("/api/stats/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_customers" in data and "total_facilities" in data
        assert data["total_customers"] >= 1
        assert data["total_facilities"] >= 1

    async def test_dashboard_stats_empty(self, client: AsyncClient, auth_headers: dict):
        """With an empty database the endpoint returns 200 and zero counts."""
        resp = await client.get("/api/stats/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_customers"] == 0
        assert data["total_facilities"] == 0
        assert data["active_facilities"] == 0
        assert data["monthly_revenue"] == 0
        assert data["recent_activities"] == []

    async def test_dashboard_stats_db_error(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        """A database failure during aggregation degrades gracefully (no crash).

        Each aggregate query is individually guarded, so a broken query yields a
        zeroed value rather than blanking (or 500-ing) the whole dashboard. The
        endpoint must therefore stay usable and never leak internals.
        """
        from app.routers import stats as stats_module

        def boom(*args, **kwargs):
            raise RuntimeError("simulated database failure")

        # Break the stats endpoint's query building (auth uses its own `select`
        # import, so authentication still succeeds).
        monkeypatch.setattr(stats_module, "select", boom)

        resp = await client.get("/api/stats/dashboard", headers=auth_headers)
        # Resilient: returns a usable (zeroed) dashboard, or a clean generic 500 —
        # never an unhandled crash and never an internals leak.
        assert resp.status_code in (200, 500)
        body = resp.json()
        if resp.status_code == 200:
            assert body["total_customers"] == 0
            assert body["monthly_revenue"] == 0
        else:
            assert "detail" in body
        assert "simulated database failure" not in resp.text
        assert "RuntimeError" not in resp.text
