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

        # It now surfaces under the facility's detail (generic registry shape).
        fd = await client.get(f"/api/facilities/{test_facility.id}/detail", headers=auth_headers)
        assert fd.status_code == 200
        fprops = fd.json()["collateral"]["properties"]
        assert any(p["prop_type"] == "Office" for p in fprops)

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


class TestGenericCollateralLinking:
    """The same linking applies to every collateral entity, not just properties."""

    async def test_guarantor_for_orphan_creates_stub_customer(
        self, client: AsyncClient, auth_headers: dict
    ):
        acc = "ORPHAN-G-1"
        r = await client.post(
            f"/api/crm/guarantors/{acc}", headers=auth_headers,
            json={"guarantor_name": "Mr X", "cheque_amount": 5000},
        )
        assert r.status_code == 200, r.text
        # A stub customer now exists for the orphan account and lists the guarantor.
        custs = await client.get(f"/api/customers/?search={acc}", headers=auth_headers)
        items = custs.json().get("items", custs.json()) if custs.status_code == 200 else []
        match = [c for c in items if c.get("account_no") == acc]
        assert match, "guarantor should have auto-created its customer"
        detail = await client.get(f"/api/customers/{match[0]['id']}/detail", headers=auth_headers)
        assert any(g["guarantor_name"] == "Mr X" for g in detail.json()["guarantors"])

    async def test_fd_and_partner_pinned_to_facility_show_under_it(
        self, client: AsyncClient, auth_headers: dict, test_customer, test_facility
    ):
        acc = test_customer.account_no
        fid = test_facility.id
        fd = await client.post(
            f"/api/crm/fixed-deposits/{acc}", headers=auth_headers,
            json={"facility_id": fid, "fd_number": "FD-777", "amount": 250000, "currency": "AED"},
        )
        assert fd.status_code == 200, fd.text
        prt = await client.post(
            f"/api/crm/partners/{acc}", headers=auth_headers,
            json={"facility_id": fid, "name": "Partner One", "share": "30%"},
        )
        assert prt.status_code == 200, prt.text

        detail = await client.get(f"/api/facilities/{fid}/detail", headers=auth_headers)
        assert detail.status_code == 200
        collateral = detail.json()["collateral"]
        assert any(f["fd_number"] == "FD-777" for f in collateral["fixed_deposits"])
        assert any(p["name"] == "Partner One" for p in collateral["partners"])


class TestGuarantorRelationships:
    """A guarantor is itself an account: it gets a profile and the relationship is
    recorded on both sides."""

    async def test_guarantor_account_gets_profile_and_relationship(
        self, client: AsyncClient, auth_headers: dict, test_customer
    ):
        borrower_acc = test_customer.account_no
        borrower_id = test_customer.id
        guar_acc = "GUAR-555"

        r = await client.post(
            f"/api/crm/guarantors/{borrower_acc}", headers=auth_headers,
            json={"guarantor_name": "Strong Guarantor LLC", "guarantor_account": guar_acc,
                  "cheque_no": "CH-1", "cheque_amount": 75000},
        )
        assert r.status_code == 200, r.text

        # 1) The guarantor now has its OWN profile.
        custs = await client.get(f"/api/customers/?search={guar_acc}", headers=auth_headers)
        items = custs.json().get("items", custs.json())
        gmatch = [c for c in items if c.get("account_no") == guar_acc]
        assert gmatch, "guarantor account should have an auto-created profile"
        guar_id = gmatch[0]["id"]

        # 2) The borrower's profile links the guarantor to its profile + lists the relation received.
        bdetail = (await client.get(f"/api/customers/{borrower_id}/detail", headers=auth_headers)).json()
        g = [x for x in bdetail["guarantors"] if x["guarantor_account"] == guar_acc]
        assert g and g[0]["guarantor_customer_id"] == guar_id
        assert any(rel["counterparty_account"] == guar_acc for rel in bdetail["relationships"]["received"])

        # 3) The guarantor's OWN profile records that it guarantees the borrower (given).
        gdetail = (await client.get(f"/api/customers/{guar_id}/detail", headers=auth_headers)).json()
        given = gdetail["relationships"]["given"]
        assert any(rel["counterparty_account"] == borrower_acc and rel["relation"] == "guarantor" for rel in given)
