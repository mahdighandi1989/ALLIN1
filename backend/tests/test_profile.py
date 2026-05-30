"""Tests for the current-user profile + change-password flow."""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestProfile:
    async def test_me_returns_current_user(self, client: AsyncClient, auth_headers: dict, test_user: User):
        r = await client.get("/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["username"] == test_user.username

    async def test_update_profile(self, client: AsyncClient, auth_headers: dict):
        r = await client.put("/api/auth/me", json={"full_name": "Updated Name"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["full_name"] == "Updated Name"

    async def test_change_password_flow(self, client: AsyncClient, auth_headers: dict):
        # wrong current password rejected
        bad = await client.post(
            "/api/auth/change-password",
            json={"current_password": "wrongpw1", "new_password": "brandnew123"},
            headers=auth_headers,
        )
        assert bad.status_code == 400

        # correct change succeeds
        ok = await client.post(
            "/api/auth/change-password",
            json={"current_password": "testpass123", "new_password": "brandnew123"},
            headers=auth_headers,
        )
        assert ok.status_code == 200

        # can log in with the new password
        relog = await client.post(
            "/api/auth/login", data={"username": "testuser", "password": "brandnew123"}
        )
        assert relog.status_code == 200

    async def test_change_password_weak_rejected(self, client: AsyncClient, auth_headers: dict):
        r = await client.post(
            "/api/auth/change-password",
            json={"current_password": "testpass123", "new_password": "short"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def test_profile_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/auth/me")).status_code == 401
