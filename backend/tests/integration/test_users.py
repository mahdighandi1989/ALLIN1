"""Integration tests for the admin user-management endpoints (/api/users).

Regression coverage for the reported 500 on
``GET /api/users/?page=1&page_size=100`` — the users list must return a 200
paginated payload (``items``/``page``/``page_size``/``total``) for an admin,
not a server error.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.verify
async def test_list_users_pagination(client: AsyncClient, admin_headers: dict):
    """GET /api/users/?page=1&page_size=100 returns 200 with a pagination shape."""
    resp = await client.get(
        "/api/users/?page=1&page_size=100", headers=admin_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    assert body["page"] == 1
    assert body["page_size"] == 100
    assert "total" in body


async def test_list_users_serializes_all_fields(
    client: AsyncClient, admin_headers: dict, admin_user: User
):
    """The list serializes every admin user (incl. nullable/auth fields) without 500."""
    resp = await client.get("/api/users/", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 1
    me = next((u for u in body["items"] if u["username"] == "admin"), None)
    assert me is not None
    # nullable + provider fields must be present and serializable
    assert me["auth_provider"] == "local"
    assert "picture" in me
    assert me["role"] == "admin"


async def test_list_users_requires_admin(
    client: AsyncClient, auth_headers: dict
):
    """A non-admin (editor) is forbidden from listing users."""
    resp = await client.get("/api/users/", headers=auth_headers)
    assert resp.status_code == 403
