"""Tests for customer-detail and portfolio reporting endpoints."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.offer_letter import OfferLetter, OfferStatus


async def _seed(db_session):
    c1 = Customer(account_no="REP-1", name="Report Corp", branch="Dubai Main")
    c2 = Customer(account_no="REP-2", name="Report SME", branch="Sharjah")
    db_session.add_all([c1, c2])
    await db_session.commit()
    await db_session.refresh(c1)
    await db_session.refresh(c2)
    db_session.add_all([
        Facility(customer_id=c1.id, facility_type=FacilityType.LOAN, amount=Decimal("5000000"),
                 outstanding=Decimal("4000000"), status=FacilityStatus.ACTIVE, risk_rating="low"),
        Facility(customer_id=c1.id, facility_type=FacilityType.OVERDRAFT, amount=Decimal("1000000"),
                 outstanding=Decimal("500000"), status=FacilityStatus.ACTIVE, risk_rating="high"),
        Facility(customer_id=c2.id, facility_type=FacilityType.LC, amount=Decimal("2000000"),
                 outstanding=Decimal("2000000"), status=FacilityStatus.ACTIVE, risk_rating="medium"),
    ])
    db_session.add(
        OfferLetter(customer_id=c1.id, expiry_date=date.today() + timedelta(days=30),
                    principal_amount=Decimal("3000000"),
                    interest_rate=Decimal("6"), tenor_months=24, status=OfferStatus.SENT)
    )
    await db_session.commit()
    return c1, c2


class TestCustomerDetail:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/customers/x/detail")).status_code == 401

    async def test_detail_aggregates(self, client: AsyncClient, auth_headers: dict, db_session):
        c1, _ = await _seed(db_session)
        r = await client.get(f"/api/customers/{c1.id}/detail", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["customer"]["id"] == c1.id
        assert body["summary"]["total_facilities"] == 2
        assert body["summary"]["active_facilities"] == 2
        assert body["summary"]["total_offers"] == 1
        assert body["summary"]["total_exposure"] == pytest.approx(6000000.0)
        assert body["summary"]["total_outstanding"] == pytest.approx(4500000.0)
        assert len(body["facilities"]) == 2
        assert len(body["offer_letters"]) == 1

    async def test_detail_unknown_404(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/customers/nope/detail", headers=auth_headers)
        assert r.status_code == 404


class TestReports:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/reports/portfolio")).status_code == 401
        assert (await client.get("/api/reports/top-exposures")).status_code == 401

    async def test_portfolio(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed(db_session)
        r = await client.get("/api/reports/portfolio", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["summary"]["total_customers"] == 2
        assert body["summary"]["total_facilities"] == 3
        assert body["summary"]["total_exposure"] == pytest.approx(8000000.0)
        # utilisation = outstanding / exposure * 100 = 6.5M / 8M = 81.2%
        assert body["summary"]["utilisation_pct"] == pytest.approx(81.2, abs=0.5)
        types = {x["label"] for x in body["facilities_by_type"]}
        assert {"loan", "overdraft", "lc"} <= types
        risks = {x["label"] for x in body["facilities_by_risk"]}
        assert {"low", "medium", "high"} <= risks

    async def test_top_exposures(self, client: AsyncClient, auth_headers: dict, db_session):
        c1, c2 = await _seed(db_session)
        r = await client.get("/api/reports/top-exposures?limit=5", headers=auth_headers)
        assert r.status_code == 200
        items = r.json()["items"]
        assert items[0]["name"] == "Report Corp"  # 6M > 2M
        assert items[0]["exposure"] == pytest.approx(6000000.0)
        assert items[0]["facilities"] == 2
