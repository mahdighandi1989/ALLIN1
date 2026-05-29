"""Tests for authentication enforcement after removing the AUTH_DISABLED backdoor.

These cover the acceptance criteria of task 62de5589:
  1. Without a valid JWT, /api/customers returns 401.
  2. The AUTH_DISABLED setting no longer exists / is ignored — authentication is
     always enforced.
"""
import pytest
from httpx import AsyncClient

from app.config import settings, Settings


class TestAuthEnforcement:
    """Protected resource endpoints must require a valid JWT (no bypass)."""

    async def test_customers_requires_auth(self, client: AsyncClient):
        """AC#1: without a valid JWT, /api/customers returns 401."""
        response = await client.get("/api/customers/")
        assert response.status_code == 401

    async def test_customers_accessible_with_valid_token(
        self, client: AsyncClient, auth_headers: dict
    ):
        """With a valid JWT the customers endpoint is reachable (200)."""
        response = await client.get("/api/customers/", headers=auth_headers)
        assert response.status_code == 200

    async def test_customers_rejects_invalid_token(self, client: AsyncClient):
        """A garbage bearer token is rejected with 401."""
        response = await client.get(
            "/api/customers/", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401

    async def test_facilities_requires_auth(self, client: AsyncClient):
        """Facilities endpoints are also protected."""
        response = await client.get("/api/facilities/")
        assert response.status_code == 401

    async def test_stats_requires_auth(self, client: AsyncClient):
        """Stats/dashboard endpoint is also protected."""
        response = await client.get("/api/stats/dashboard")
        assert response.status_code == 401

    def test_auth_disabled_setting_removed(self):
        """AC#2 (static): AUTH_DISABLED must not exist in the settings model."""
        assert "AUTH_DISABLED" not in Settings.model_fields
        assert not hasattr(settings, "AUTH_DISABLED")

    async def test_auth_disabled_env_has_no_effect(
        self, client: AsyncClient, monkeypatch
    ):
        """Even if AUTH_DISABLED=true is set in the environment, auth is enforced.

        The flag has been removed from the code entirely, so it can no longer
        create an authentication bypass.
        """
        monkeypatch.setenv("AUTH_DISABLED", "true")
        response = await client.get("/api/customers/")
        assert response.status_code == 401
