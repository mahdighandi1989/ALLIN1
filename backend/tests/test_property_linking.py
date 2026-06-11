"""Property ↔ customer ↔ facility linking.

Covers the "no more islands" behaviour:
  * creating a property from the register auto-creates a stub customer for an
    orphan account_no, and the property then shows under that customer;
  * a property linked to a facility surfaces under that facility's detail.
"""
import pytest
from httpx import AsyncClient

from app.models.customer import Customer
from app.models.facility import Facility


class TestRegisterCreateLinksCustomer:
    async def test_create_for_orphan_account_creates_stub_and_links(
        self, client: AsyncClient, auth_headers: dict
    ):
        acc = "ORPHAN-9001"
        body = {"account_no": acc, "customer_name": "Acme Holding", "city": "Dubai",
                "prop_type": "Villa", "valuation": 1000000, "valuation_currency": "AED"}
        r = await client.post("/api/properties/", headers=auth_headers, json=body)
        assert r.status_code == 201, r.text
        assert r.json()["account_no"] == acc

        # The register now resolves the property to a (newly created) customer.
        lst = await client.get(f"/api/properties/?search={acc}", headers=auth_headers)
        assert lst.status_code == 200
        rows = [it for it in lst.json()["items"] if it["ac_no"] == acc]
        assert rows and rows[0]["customer_id"], "property should link to an auto-created customer"
        cid = rows[0]["customer_id"]

        # And the property shows under that customer's profile.
        detail = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert detail.status_code == 200
        props = detail.json()["properties"]
        assert any(p["account_no"] == acc for p in props)
        # The stub carries the name hint we supplied.
        assert detail.json()["customer"]["name"] == "Acme Holding"

    async def test_create_requires_account_no(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/properties/", headers=auth_headers, json={"account_no": "  "})
        assert r.status_code == 422


class TestFacilityLinkedProperty:
    async def test_property_shows_under_its_facility(
        self, client: AsyncClient, auth_headers: dict, test_customer: Customer, test_facility: Facility
    ):
        acc = test_customer.account_no
        # Add a property under the customer, linked to the specific facility.
        r = await client.post(
            f"/api/crm/properties/{acc}", headers=auth_headers,
            json={"facility_id": test_facility.id, "city": "Abu Dhabi", "prop_type": "Office",
                  "mortgage_amount": 500000, "valuation_currency": "AED"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["facility_id"] == test_facility.id

        # It now surfaces under the facility's detail.
        fd = await client.get(f"/api/facilities/{test_facility.id}/detail", headers=auth_headers)
        assert fd.status_code == 200
        fprops = fd.json().get("properties", [])
        assert any(p["type"] == "Office" for p in fprops)

    async def test_edit_and_delete_from_register(
        self, client: AsyncClient, auth_headers: dict
    ):
        acc = "ORPHAN-9002"
        created = await client.post(
            "/api/properties/", headers=auth_headers,
            json={"account_no": acc, "customer_name": "Beta LLC", "city": "Sharjah"},
        )
        pid = created.json()["id"]

        upd = await client.put(f"/api/properties/{pid}", headers=auth_headers, json={"city": "Ajman"})
        assert upd.status_code == 200
        assert upd.json()["city"] == "Ajman"

        dele = await client.delete(f"/api/properties/{pid}", headers=auth_headers)
        assert dele.status_code == 200
        # Gone from the register.
        lst = await client.get(f"/api/properties/?search={acc}", headers=auth_headers)
        assert not any(it["id"] == pid for it in lst.json()["items"])
