"""Tests for authentication enforcement.

AUTH_DISABLED was later re-introduced as a TEMPORARY login toggle. The suite-wide
autouse fixture pins AUTH_DISABLED=False, so these tests verify that *with the
toggle off* authentication is strictly enforced:
  1. Without a valid JWT, /api/customers returns 401.
  2. The AUTH_DISABLED toggle exists and, when off, never creates a bypass.
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

    def test_auth_disabled_toggle_exists(self):
        """AUTH_DISABLED is a supported boolean toggle on the settings model."""
        assert "AUTH_DISABLED" in Settings.model_fields
        assert isinstance(settings.AUTH_DISABLED, bool)

    async def test_auth_enforced_when_toggle_off(
        self, client: AsyncClient, monkeypatch
    ):
        """With AUTH_DISABLED off (the pinned test default), auth is enforced.

        A stale AUTH_DISABLED=true in the *environment* does not flip the
        already-loaded setting, so the bypass cannot be triggered accidentally.
        """
        monkeypatch.setenv("AUTH_DISABLED", "true")
        response = await client.get("/api/customers/")
        assert response.status_code == 401
