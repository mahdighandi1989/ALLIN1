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


class TestFxService:
    """Direct unit tests for the fx service helpers (to_base / load_rates)."""

    def test_to_base_converts_with_rate(self):
        from app.services.fx import to_base

        rates = {"AED": 1.0, "USD": 3.6725}
        assert to_base(1000, "USD", rates) == pytest.approx(3672.5)
        assert to_base(Decimal("500"), "AED", rates) == pytest.approx(500.0)

    def test_to_base_edge_cases(self):
        from app.services.fx import to_base

        rates = {"AED": 1.0, "USD": 3.6725}
        assert to_base(None, "USD", rates) == 0.0           # None amount
        assert to_base("not-a-number", "USD", rates) == 0.0  # unparseable amount
        assert to_base(100, None, rates) == pytest.approx(100.0)  # None currency -> base
        # Unknown currency is treated as 1:1 (not dropped).
        assert to_base(100, "JPY", rates) == pytest.approx(100.0)

    async def test_load_rates_from_db(self, db_session):
        from app.services.fx import load_rates

        await _seed_rates(db_session)
        rates = await load_rates(db=db_session)
        assert rates[BASE_CURRENCY] == 1.0
        assert rates["USD"] == pytest.approx(3.6725)

    async def test_load_rates_empty_db_has_base(self, db_session):
        from app.services.fx import load_rates

        rates = await load_rates(db=db_session)
        # Base currency is always present even with no rows.
        assert rates[BASE_CURRENCY] == 1.0
