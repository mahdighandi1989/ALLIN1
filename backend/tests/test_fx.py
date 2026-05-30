"""Tests for multi-currency exchange rates + currency-normalised dashboard."""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.exchange_rate import ExchangeRate, BASE_CURRENCY


async def _seed_rates(db_session):
    db_session.add_all([
        ExchangeRate(currency="AED", rate_to_base=Decimal("1.0")),
        ExchangeRate(currency="USD", rate_to_base=Decimal("3.6725")),
        ExchangeRate(currency="EUR", rate_to_base=Decimal("3.95")),
    ])
    await db_session.commit()


class TestFx:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/fx/")).status_code == 401

    async def test_list_rates(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed_rates(db_session)
        r = await client.get("/api/fx/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["base_currency"] == BASE_CURRENCY
        codes = {x["currency"] for x in r.json()["rates"]}
        assert {"AED", "USD", "EUR"} <= codes

    async def test_convert(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed_rates(db_session)
        r = await client.get(
            "/api/fx/convert?amount=1000&from_currency=USD&to_currency=AED", headers=auth_headers
        )
        assert r.status_code == 200
        assert r.json()["converted"] == pytest.approx(3672.5)

    async def test_non_admin_cannot_update(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed_rates(db_session)
        r = await client.put("/api/fx/", json={"rates": {"USD": 4.0}}, headers=auth_headers)
        assert r.status_code == 403

    async def test_admin_update_and_validation(self, client: AsyncClient, admin_headers: dict, db_session):
        await _seed_rates(db_session)
        ok = await client.put("/api/fx/", json={"rates": {"USD": 4.0, "GBP": 4.65}}, headers=admin_headers)
        assert ok.status_code == 200
        usd = next(x for x in ok.json()["rates"] if x["currency"] == "USD")
        assert usd["rate_to_base"] == pytest.approx(4.0)

        assert (await client.put("/api/fx/", json={"rates": {"US": 1.0}}, headers=admin_headers)).status_code == 422
        assert (await client.put("/api/fx/", json={"rates": {"USD": -1}}, headers=admin_headers)).status_code == 422

    async def test_dashboard_normalises_currencies(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        await _seed_rates(db_session)
        c = Customer(account_no="FX-D", name="Mixed Co")
        db_session.add(c)
        await db_session.flush()
        db_session.add_all([
            Facility(customer_id=c.id, facility_type=FacilityType.LOAN, amount=Decimal("1000000"),
                     currency="AED", status=FacilityStatus.ACTIVE),
            Facility(customer_id=c.id, facility_type=FacilityType.LOAN, amount=Decimal("1000000"),
                     currency="USD", status=FacilityStatus.ACTIVE),
        ])
        await db_session.commit()

        data = (await client.get("/api/stats/dashboard", headers=auth_headers)).json()
        # 1,000,000 AED + 1,000,000 USD*3.6725 = 4,672,500 AED
        assert data["total_exposure"]["currency"] == BASE_CURRENCY
        assert data["total_exposure"]["amount"] == pytest.approx(4_672_500.0, rel=1e-3)
