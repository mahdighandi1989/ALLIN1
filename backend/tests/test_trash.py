"""Tests for the recycle bin (list + restore soft-deleted records)."""
import pytest
from httpx import AsyncClient

from app.models.customer import Customer


class TestTrash:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/trash/")).status_code == 401

    async def test_empty_trash(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/trash/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_deleted_customer_appears_and_restores(
        self, client: AsyncClient, auth_headers: dict, test_customer: Customer
    ):
        # delete -> trash shows it
        assert (
            await client.delete(f"/api/customers/{test_customer.id}", headers=auth_headers)
        ).status_code == 204
        trash = await client.get("/api/trash/", headers=auth_headers)
        assert trash.status_code == 200
        assert trash.json()["counts"]["customers"] == 1
        assert any(i["id"] == test_customer.id and i["type"] == "customer"
                   for i in trash.json()["items"])

        # restore via the trash endpoint
        r = await client.post(
            f"/api/trash/customer/{test_customer.id}/restore", headers=auth_headers
        )
        assert r.status_code == 200 and r.json()["restored"] is True

        # gone from trash, back in the customer list
        assert (await client.get("/api/trash/", headers=auth_headers)).json()["total"] == 0
        listing = await client.get("/api/customers/", headers=auth_headers)
        assert any(c["id"] == test_customer.id for c in listing.json()["items"])

    async def test_deleted_facility_appears_in_trash(
        self, client: AsyncClient, auth_headers: dict, test_facility
    ):
        await client.delete(f"/api/facilities/{test_facility.id}", headers=auth_headers)
        trash = await client.get("/api/trash/", headers=auth_headers)
        assert trash.json()["counts"]["facilities"] == 1

    async def test_restore_unknown_404(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/trash/customer/NOPE/restore", headers=auth_headers)
        assert r.status_code == 404

    async def test_restore_unknown_entity_400(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/trash/widget/x/restore", headers=auth_headers)
        assert r.status_code == 400
