"""Tests for the TEMPORARY AUTH_DISABLED login bypass.

The suite-wide autouse fixture pins AUTH_DISABLED=False, so these tests opt in
explicitly via monkeypatch to exercise the bypass path.
"""
import pytest
from httpx import AsyncClient

from app.config import settings as app_settings


class TestAuthDisabledBypass:
    async def test_config_endpoint_reports_flag(self, client: AsyncClient):
        """GET /api/auth/config is public and reflects AUTH_DISABLED."""
        resp = await client.get("/api/auth/config")
        assert resp.status_code == 200
        assert resp.json()["auth_disabled"] is False  # enforced inside tests

    async def test_protected_endpoint_open_when_auth_disabled(
        self, client: AsyncClient, monkeypatch
    ):
        """With AUTH_DISABLED on, a protected endpoint works WITHOUT a token."""
        monkeypatch.setattr(app_settings, "AUTH_DISABLED", True)

        # No Authorization header at all.
        resp = await client.get("/api/customers/")
        assert resp.status_code == 200
        assert "items" in resp.json()

        # And the config endpoint now advertises the bypass.
        cfg = await client.get("/api/auth/config")
        assert cfg.json()["auth_disabled"] is True

    async def test_auth_still_enforced_when_flag_off(self, client: AsyncClient):
        """Default (flag off): the same endpoint requires authentication."""
        resp = await client.get("/api/customers/")
        assert resp.status_code == 401
