"""Unit tests for the dashboard statistics endpoint (/api/stats/dashboard)."""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.customer import Customer, AccountType, CustomerStatus


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
