"""Profile child entities — mortgaged properties, fixed deposits, partners.

They are added/edited/removed via /api/crm/* and surfaced (with summary counts)
through GET /api/customers/{id}/detail. Mirrors requirement A12 of the legacy
Excel system: capture FD + property details per customer profile, many each.
"""
import pytest
from httpx import AsyncClient

from app.models.customer import Customer


class TestProfileEntities:
    async def test_property_crud_and_detail(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id

        # add
        r = await client.post(
            f"/api/crm/properties/{acc}", headers=auth_headers,
            json={"plate_no": "PL-123", "city": "Dubai", "mortgage_amount": 1500000,
                  "valuation": 2000000, "valuation_currency": "AED", "insurance_no": "INS-9"},
        )
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        assert r.json()["plate_no"] == "PL-123"
        assert r.json()["mortgage_amount"] == 1500000

        # surfaced in detail with summary counts
        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d.status_code == 200, d.text
        body = d.json()
        assert len(body["properties"]) == 1
        assert body["summary"]["total_properties"] == 1
        assert body["summary"]["total_mortgage_amount"] == 1500000

        # edit
        u = await client.patch(f"/api/crm/properties/{pid}", headers=auth_headers, json={"city": "Abu Dhabi"})
        assert u.status_code == 200
        assert u.json()["city"] == "Abu Dhabi"
        assert u.json()["plate_no"] == "PL-123"  # untouched field preserved

        # soft-delete -> gone from detail
        x = await client.delete(f"/api/crm/properties/{pid}", headers=auth_headers)
        assert x.status_code == 200
        d2 = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d2.json()["summary"]["total_properties"] == 0

    async def test_fixed_deposit_crud(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id
        r = await client.post(
            f"/api/crm/fixed-deposits/{acc}", headers=auth_headers,
            json={"fd_number": "FD-1", "amount": 500000, "currency": "USD", "rate": "4.5%"},
        )
        assert r.status_code == 200, r.text
        fid = r.json()["id"]
        assert r.json()["amount"] == 500000
        assert r.json()["currency"] == "USD"

        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d.json()["summary"]["total_fixed_deposits"] == 1
        assert d.json()["summary"]["total_fd_amount"] == 500000

        assert (await client.patch(f"/api/crm/fixed-deposits/{fid}", headers=auth_headers,
                                   json={"rate": "5%"})).json()["rate"] == "5%"
        assert (await client.delete(f"/api/crm/fixed-deposits/{fid}", headers=auth_headers)).status_code == 200

    async def test_partner_crud(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id
        r = await client.post(
            f"/api/crm/partners/{acc}", headers=auth_headers,
            json={"name": "Ali Reza", "nationality": "IR", "share": "60%"},
        )
        assert r.status_code == 200, r.text
        ptid = r.json()["id"]

        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d.json()["summary"]["total_partners"] == 1
        assert d.json()["partners"][0]["name"] == "Ali Reza"
        assert d.json()["partners"][0]["share"] == "60%"
        assert (await client.delete(f"/api/crm/partners/{ptid}", headers=auth_headers)).status_code == 200

    async def test_partner_name_required(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        r = await client.post(f"/api/crm/partners/{test_customer.account_no}", headers=auth_headers, json={"nationality": "IR"})
        assert r.status_code == 422

    async def test_requires_auth(self, client: AsyncClient, test_customer: Customer):
        r = await client.post(f"/api/crm/properties/{test_customer.account_no}", json={"city": "X"})
        assert r.status_code == 401

    async def test_update_missing_returns_404(self, client: AsyncClient, auth_headers: dict):
        r = await client.patch("/api/crm/properties/NOPE", headers=auth_headers, json={"city": "X"})
        assert r.status_code == 404
