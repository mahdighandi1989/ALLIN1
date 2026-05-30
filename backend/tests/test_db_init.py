"""Tests for the self-healing DB bootstrap (schema sync + demo seeding)."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, func

from app.db_init import _seed_rows
from app.models.customer import Customer
from app.models.facility import Facility, FacilityStatus


def test_seed_rows_are_valid_and_linked():
    customers, facilities = _seed_rows()
    assert len(customers) >= 5
    assert len(facilities) >= 5
    # Every facility is linked to one of the seeded customers.
    seeded = set(customers)
    assert all(f.customer in seeded for f in facilities)
    # Amounts/rates are sane decimals.
    assert all(f.amount > 0 for f in facilities)


class TestSeededDashboard:
    async def test_seeded_data_populates_dashboard(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        """Inserting the demo rows yields a populated, realistic dashboard."""
        customers, facilities = _seed_rows()
        db_session.add_all(customers)
        await db_session.flush()
        db_session.add_all(facilities)
        await db_session.commit()

        resp = await client.get("/api/stats/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_customers"] == len(customers)
        assert data["total_facilities"] == len(facilities)
        assert data["active_facilities"] >= 1
        assert data["monthly_revenue"] > 0
        assert data["total_exposure"]["amount"] > 0
        assert len(data["recent_activities"]) >= 1

    async def test_seed_counts_match_db(self, db_session):
        customers, facilities = _seed_rows()
        db_session.add_all(customers)
        await db_session.flush()
        db_session.add_all(facilities)
        await db_session.commit()

        nc = (await db_session.execute(select(func.count(Customer.id)))).scalar()
        active = (
            await db_session.execute(
                select(func.count(Facility.id)).where(
                    Facility.status == FacilityStatus.ACTIVE
                )
            )
        ).scalar()
        assert nc == len(customers)
        assert active >= 1
