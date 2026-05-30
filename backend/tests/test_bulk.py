"""Tests for bulk (multi-select) delete actions."""
import pytest
from httpx import AsyncClient

from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus


class TestBulkDelete:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.post("/api/customers/bulk/delete", json={"ids": ["x"]})).status_code == 401

    async def test_bulk_delete_customers(self, client: AsyncClient, auth_headers: dict, db_session):
        ids = []
        for i in range(3):
            c = Customer(account_no=f"BD-{i}", name=f"Bulk {i}",
                         account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE)
            db_session.add(c)
            await db_session.flush()
            ids.append(c.id)
        await db_session.commit()

        r = await client.post("/api/customers/bulk/delete", json={"ids": ids[:2]}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["deleted"] == 2

        # The two are gone from the listing, the third remains.
        remaining = {c["id"] for c in (await client.get("/api/customers/?page_size=100", headers=auth_headers)).json()["items"]}
        assert ids[0] not in remaining and ids[1] not in remaining
        assert ids[2] in remaining

        # And they show up in the recycle bin.
        assert (await client.get("/api/trash/", headers=auth_headers)).json()["counts"]["customers"] >= 2

    async def test_bulk_delete_facilities(self, client: AsyncClient, auth_headers: dict, test_customer, db_session):
        ids = []
        for i in range(2):
            f = Facility(customer_id=test_customer.id, facility_type=FacilityType.LOAN,
                         amount=1000 + i, currency="AED", status=FacilityStatus.ACTIVE)
            db_session.add(f)
            await db_session.flush()
            ids.append(f.id)
        await db_session.commit()

        r = await client.post("/api/facilities/bulk/delete", json={"ids": ids}, headers=auth_headers)
        assert r.status_code == 200 and r.json()["deleted"] == 2

    async def test_empty_ids_rejected(self, client: AsyncClient, auth_headers: dict):
        assert (await client.post("/api/customers/bulk/delete", json={"ids": []}, headers=auth_headers)).status_code == 422

    async def test_unknown_ids_delete_zero(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/customers/bulk/delete", json={"ids": ["nope1", "nope2"]}, headers=auth_headers)
        assert r.status_code == 200 and r.json()["deleted"] == 0
