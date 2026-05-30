"""Tests for audit logging + the admin audit-log viewer."""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestAuditLog:
    async def test_requires_admin(self, client: AsyncClient, auth_headers: dict):
        # regular user -> 403
        assert (await client.get("/api/audit/", headers=auth_headers)).status_code == 403

    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/audit/")).status_code == 401

    async def test_customer_crud_is_audited(
        self, client: AsyncClient, admin_headers: dict
    ):
        # create a customer as admin
        c = await client.post(
            "/api/customers/",
            json={"account_no": "AUDIT-X", "name": "Audited Co", "account_type": "sme"},
            headers=admin_headers,
        )
        assert c.status_code == 201
        cid = c.json()["id"]
        await client.put(f"/api/customers/{cid}", json={"name": "Renamed"}, headers=admin_headers)
        await client.delete(f"/api/customers/{cid}", headers=admin_headers)

        audit = await client.get("/api/audit/", headers=admin_headers)
        assert audit.status_code == 200
        actions = {(e["action"], e["entity_type"]) for e in audit.json()["items"]}
        assert ("create", "customer") in actions
        assert ("update", "customer") in actions
        assert ("delete", "customer") in actions
        # entries carry the actor + an IP.
        entry = next(e for e in audit.json()["items"] if e["entity_type"] == "customer")
        assert entry["username"] is not None
        assert entry["created_at"] is not None

    async def test_filter_by_action_and_entity(
        self, client: AsyncClient, admin_headers: dict
    ):
        await client.post(
            "/api/customers/",
            json={"account_no": "FLT-1", "name": "Filter Co", "account_type": "retail"},
            headers=admin_headers,
        )
        r = await client.get(
            "/api/audit/?action=create&entity_type=customer", headers=admin_headers
        )
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert all(
            e["action"] == "create" and e["entity_type"] == "customer"
            for e in r.json()["items"]
        )

    async def test_user_management_is_audited(
        self, client: AsyncClient, admin_headers: dict
    ):
        await client.post(
            "/api/users/",
            json={
                "username": "audited", "email": "audited@x.ae",
                "password": "secret123", "full_name": "Audited User",
            },
            headers=admin_headers,
        )
        r = await client.get("/api/audit/?entity_type=user", headers=admin_headers)
        assert r.status_code == 200
        assert any(e["action"] == "create" for e in r.json()["items"])
