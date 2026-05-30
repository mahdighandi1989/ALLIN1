"""Tests for system settings (editable DB values + read-only runtime view)."""
import pytest
from httpx import AsyncClient


class TestSettings:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/settings/")).status_code == 401

    async def test_get_returns_editable_and_runtime(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/settings/", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        keys = {e["key"] for e in body["editable"]}
        assert {"app_name", "default_currency", "expiry_warning_days"} <= keys
        assert "environment" in body["runtime"]
        assert "auth_disabled" in body["runtime"]
        # secrets are never exposed
        assert "secret_key" not in {k.lower() for k in body["runtime"]}

    async def test_non_admin_can_read_not_write(self, client: AsyncClient, auth_headers: dict):
        # auth_headers is a regular user.
        assert (await client.get("/api/settings/", headers=auth_headers)).status_code == 200
        r = await client.put("/api/settings/", json={"values": {"app_name": "X"}}, headers=auth_headers)
        assert r.status_code == 403

    async def test_admin_update_persists(self, client: AsyncClient, admin_headers: dict):
        u = await client.put(
            "/api/settings/",
            json={"values": {"app_name": "My Bank", "expiry_warning_days": "45"}},
            headers=admin_headers,
        )
        assert u.status_code == 200
        vals = {e["key"]: e["value"] for e in u.json()["editable"]}
        assert vals["app_name"] == "My Bank"
        assert vals["expiry_warning_days"] == "45"

        # persists across requests
        g = await client.get("/api/settings/", headers=admin_headers)
        vals2 = {e["key"]: e["value"] for e in g.json()["editable"]}
        assert vals2["app_name"] == "My Bank"

    async def test_bad_number_422(self, client: AsyncClient, admin_headers: dict):
        r = await client.put("/api/settings/", json={"values": {"expiry_warning_days": "abc"}}, headers=admin_headers)
        assert r.status_code == 422

    async def test_unknown_key_400(self, client: AsyncClient, admin_headers: dict):
        r = await client.put("/api/settings/", json={"values": {"nope": "x"}}, headers=admin_headers)
        assert r.status_code == 400
