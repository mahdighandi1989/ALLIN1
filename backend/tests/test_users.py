"""Tests for admin user management (/api/users) and admin RBAC."""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestUserManagement:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/users/")).status_code == 401

    async def test_non_admin_forbidden(self, client: AsyncClient, auth_headers: dict):
        # auth_headers is a regular (non-admin) user.
        assert (await client.get("/api/users/", headers=auth_headers)).status_code == 403

    async def test_admin_can_list(self, client: AsyncClient, admin_headers: dict):
        r = await client.get("/api/users/", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    async def test_admin_crud_lifecycle(self, client: AsyncClient, admin_headers: dict):
        # create
        c = await client.post(
            "/api/users/",
            json={
                "username": "charlie", "email": "charlie@bank.ae",
                "password": "secret123", "full_name": "Charlie C", "is_admin": False,
            },
            headers=admin_headers,
        )
        assert c.status_code == 201, c.text
        uid = c.json()["id"]
        assert c.json()["username"] == "charlie"
        assert c.json()["is_admin"] is False

        # get
        assert (await client.get(f"/api/users/{uid}", headers=admin_headers)).status_code == 200

        # update -> promote to admin
        u = await client.put(f"/api/users/{uid}", json={"is_admin": True}, headers=admin_headers)
        assert u.status_code == 200 and u.json()["is_admin"] is True

        # search finds them
        s = await client.get("/api/users/?search=charlie", headers=admin_headers)
        assert s.status_code == 200 and s.json()["total"] >= 1

        # deactivate
        d = await client.delete(f"/api/users/{uid}", headers=admin_headers)
        assert d.status_code == 204
        assert (await client.get(f"/api/users/{uid}", headers=admin_headers)).json()["is_active"] is False

    async def test_create_with_explicit_role(self, client: AsyncClient, admin_headers: dict):
        # An admin can create a user at a chosen access level — not just the
        # binary admin/non-admin — and is_admin stays in sync with the role.
        r = await client.post(
            "/api/users/",
            json={
                "username": "vera", "email": "vera@bank.ae",
                "password": "secret123", "full_name": "Vera V", "role": "viewer",
            },
            headers=admin_headers,
        )
        assert r.status_code == 201, r.text
        assert r.json()["role"] == "viewer"
        assert r.json()["is_admin"] is False

    async def test_create_admin_role_sets_is_admin(self, client: AsyncClient, admin_headers: dict):
        r = await client.post(
            "/api/users/",
            json={
                "username": "adina", "email": "adina@bank.ae",
                "password": "secret123", "full_name": "Adina A", "role": "admin",
            },
            headers=admin_headers,
        )
        assert r.status_code == 201, r.text
        assert r.json()["role"] == "admin" and r.json()["is_admin"] is True

    async def test_create_invalid_role_422(self, client: AsyncClient, admin_headers: dict):
        r = await client.post(
            "/api/users/",
            json={
                "username": "badrole", "email": "badrole@bank.ae",
                "password": "secret123", "full_name": "Bad Role", "role": "superuser",
            },
            headers=admin_headers,
        )
        assert r.status_code == 422

    async def test_duplicate_username_rejected(self, client: AsyncClient, admin_headers: dict, admin_user: User):
        r = await client.post(
            "/api/users/",
            json={
                "username": admin_user.username, "email": "other@bank.ae",
                "password": "secret123", "full_name": "Dup",
            },
            headers=admin_headers,
        )
        assert r.status_code == 400

    async def test_invalid_password_422(self, client: AsyncClient, admin_headers: dict):
        r = await client.post(
            "/api/users/",
            json={
                "username": "weakpw", "email": "weak@bank.ae",
                "password": "short", "full_name": "Weak",
            },
            headers=admin_headers,
        )
        assert r.status_code == 422

    async def test_cannot_deactivate_self(self, client: AsyncClient, admin_headers: dict, admin_user: User):
        r = await client.delete(f"/api/users/{admin_user.id}", headers=admin_headers)
        assert r.status_code == 400
        assert "own account" in r.json()["detail"]
