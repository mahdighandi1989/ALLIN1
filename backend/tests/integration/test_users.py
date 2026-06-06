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


@pytest.mark.verify
def test_admin_user_response_coerces_legacy_nulls():
    """Reproduces the production 500: a drifted row with NULL role/auth_provider.

    On a live DB that predates the Google-OAuth work, ``role``/``auth_provider``
    may still hold NULLs (column added without a backfilled default). Reading
    such a row used to raise a Pydantic ValidationError, which bubbled up as a
    500 for the *entire* ``GET /api/users/?page=1&page_size=100`` response. The
    serializer must coerce those NULLs to the model defaults instead. We feed a
    plain object with NULL attributes — exactly what SQLAlchemy yields for a
    dirty row — straight to ``AdminUserResponse``.
    """
    from app.schemas.admin_user import AdminUserResponse

    class _DirtyRow:
        id = "u1"
        username = "legacy"
        email = "legacy@example.com"
        full_name = None
        is_active = None       # NULL booleans on a drifted DB
        is_admin = None
        role = None            # the columns that caused the 500
        auth_provider = None
        picture = None
        created_at = None
        last_login = None

    out = AdminUserResponse.model_validate(_DirtyRow())
    assert out.role == "pending"
    assert out.auth_provider == "local"
    assert out.is_active is True
    assert out.is_admin is False
