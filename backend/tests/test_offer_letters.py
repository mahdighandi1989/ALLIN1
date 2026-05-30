"""Tests for the offer-letter workflow (API + amortisation)."""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.customer import Customer
from app.services.amortization import generate_schedule, schedule_totals


# --- amortisation math (pure) ----------------------------------------------
def test_amortization_monthly_schedule_balances_to_zero():
    s = generate_schedule(Decimal("100000"), Decimal("12"), 12, repayment_type="monthly")
    assert len(s) == 12
    assert float(s[-1].closing_balance) == 0.0
    totals = schedule_totals(s)
    # Standard annuity payment for 100k @ 1%/mo over 12 = ~8884.88
    assert 8800 < float(totals["monthly_installment"]) < 8900
    assert float(totals["total_interest"]) > 0


def test_amortization_grace_period_is_interest_only():
    s = generate_schedule(
        Decimal("120000"), Decimal("6"), 12, repayment_type="monthly",
        grace_period_months=3,
    )
    # First 3 installments pay no principal.
    assert all(i.principal_payment == 0 for i in s[:3])
    assert s[-1].closing_balance == 0


def test_amortization_bullet_repays_principal_at_maturity():
    s = generate_schedule(Decimal("50000"), Decimal("10"), 12, repayment_type="bullet")
    assert all(i.principal_payment == 0 for i in s[:-1])
    assert float(s[-1].principal_payment) == 50000.0
    assert s[-1].closing_balance == 0


def test_amortization_zero_rate():
    s = generate_schedule(Decimal("12000"), Decimal("0"), 12, repayment_type="monthly")
    assert sum(float(i.principal_payment) for i in s) == pytest.approx(12000.0, abs=1)
    assert all(i.interest_payment == 0 for i in s)


# --- API --------------------------------------------------------------------
class TestOfferLetterApi:
    async def _make_customer(self, db_session) -> str:
        c = Customer(account_no="OFF-1", name="Offer Customer")
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)
        return c.id

    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/offer-letters/")).status_code == 401

    async def test_full_lifecycle(self, client: AsyncClient, auth_headers: dict, db_session):
        cid = await self._make_customer(db_session)

        # empty
        r = await client.get("/api/offer-letters/", headers=auth_headers)
        assert r.status_code == 200 and r.json()["total"] == 0

        # create -> totals auto-computed
        create = await client.post(
            "/api/offer-letters/",
            json={
                "customer_id": cid, "expiry_date": "2027-12-31",
                "principal_amount": 1000000, "interest_rate": 7.5,
                "tenor_months": 24, "currency": "AED", "repayment_type": "monthly",
            },
            headers=auth_headers,
        )
        assert create.status_code == 201, create.text
        body = create.json()
        assert body["monthly_installment"] and body["monthly_installment"] > 0
        assert body["total_repayment_amount"] > 1000000
        oid = body["id"]

        # generate & persist schedule
        gen = await client.post(f"/api/offer-letters/{oid}/generate-schedule", headers=auth_headers)
        assert gen.status_code == 200
        schedule = gen.json()["schedule"]
        assert len(schedule) == 24
        assert schedule[-1]["closing_balance"] == 0
        assert gen.json()["customer_name"] == "Offer Customer"

        # detail returns the stored schedule
        detail = await client.get(f"/api/offer-letters/{oid}", headers=auth_headers)
        assert detail.status_code == 200
        assert len(detail.json()["schedule"]) == 24

        # update recomputes totals
        upd = await client.put(
            f"/api/offer-letters/{oid}", json={"interest_rate": 9.0}, headers=auth_headers
        )
        assert upd.status_code == 200
        assert upd.json()["interest_rate"] == 9.0

        # status transition
        st = await client.post(
            f"/api/offer-letters/{oid}/status?new_status=approved", headers=auth_headers
        )
        assert st.status_code == 200 and st.json()["status"] == "approved"

        # filter by customer + status
        assert (
            await client.get(f"/api/offer-letters/?customer_id={cid}", headers=auth_headers)
        ).json()["total"] == 1
        assert (
            await client.get("/api/offer-letters/?status=approved", headers=auth_headers)
        ).json()["total"] == 1

        # soft delete
        assert (
            await client.delete(f"/api/offer-letters/{oid}", headers=auth_headers)
        ).status_code == 204
        assert (await client.get("/api/offer-letters/", headers=auth_headers)).json()["total"] == 0
        assert (
            await client.get(f"/api/offer-letters/{oid}", headers=auth_headers)
        ).status_code == 404

    async def test_create_unknown_customer_404(self, client: AsyncClient, auth_headers: dict):
        r = await client.post(
            "/api/offer-letters/",
            json={
                "customer_id": "does-not-exist", "expiry_date": "2027-01-01",
                "principal_amount": 1000, "interest_rate": 5, "tenor_months": 12,
            },
            headers=auth_headers,
        )
        assert r.status_code == 404
        assert r.json()["detail"] == "Customer not found"

    async def test_invalid_payload_422(self, client: AsyncClient, auth_headers: dict, db_session):
        cid = await self._make_customer(db_session)
        # negative principal
        r = await client.post(
            "/api/offer-letters/",
            json={
                "customer_id": cid, "expiry_date": "2027-01-01",
                "principal_amount": -5, "interest_rate": 5, "tenor_months": 12,
            },
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def _make_offer(self, client, auth_headers, db_session) -> str:
        cid = await self._make_customer(db_session)
        r = await client.post(
            "/api/offer-letters/",
            json={
                "customer_id": cid, "expiry_date": "2027-12-31",
                "principal_amount": 500000, "interest_rate": 6.0, "tenor_months": 12,
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_export_csv(self, client: AsyncClient, auth_headers: dict, db_session):
        oid = await self._make_offer(client, auth_headers, db_session)
        r = await client.get(f"/api/offer-letters/{oid}/export.csv", headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert "attachment" in r.headers.get("content-disposition", "")
        # Header row + 12 installment rows.
        text = r.content.decode("utf-8")
        assert "installment" in text
        assert text.count("\n") >= 12

    async def test_export_pdf(self, client: AsyncClient, auth_headers: dict, db_session):
        oid = await self._make_offer(client, auth_headers, db_session)
        r = await client.get(f"/api/offer-letters/{oid}/export.pdf", headers=auth_headers)
        assert r.status_code == 200
        # Real PDF when reportlab is present; printable HTML otherwise.
        assert r.headers["content-type"] in ("application/pdf", "text/html")
        if r.headers["content-type"] == "application/pdf":
            assert r.content[:5] == b"%PDF-"

    async def test_export_unknown_404(self, client: AsyncClient, auth_headers: dict):
        assert (
            await client.get("/api/offer-letters/NOPE/export.csv", headers=auth_headers)
        ).status_code == 404
