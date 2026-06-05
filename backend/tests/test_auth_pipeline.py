"""End-to-end integration tests for the authentication pipeline.

This module is the single integration entry point that several acceptance
criteria across the security epic point their ``backend_test`` verification at
(``tests/test_auth_pipeline.py``). It exercises the pipeline as a whole rather
than any one unit:

* session lifecycle — login → access → refresh → logout/revoke must stay
  coherent between the issued token and the backend's view of it;
* permission/role enforcement — admin-only surfaces reject non-admins;
* graceful degradation — malformed tokens yield a clean 401, never a 500.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.utils.security import hash_password, create_access_token


async def _make_user(db, username, role):
    """Create a user with a specific role and return it (for RBAC scenarios)."""
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("Passw0rd1"),
        full_name=username.title(),
        is_active=True,
        role=role,
        is_admin=(role == "admin"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _headers_for(user: User) -> dict:
    token = create_access_token(data={"user_id": user.id, "username": user.username})
    return {"Authorization": f"Bearer {token}"}


async def test_integration(client: AsyncClient, test_user: User, auth_headers: dict):
    """Full happy-path auth pipeline: authenticate, access, refresh, logout.

    Validates that backend session state and token lifecycle stay coherent:
    a freshly issued token grants access, refresh mints a working token, and
    logout revokes the presented token so it can no longer be used.
    """
    # 1) Authenticated identity is readable.
    me = await client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["username"] == test_user.username

    # 2) A protected data endpoint is reachable with the token...
    assert (await client.get("/api/customers/", headers=auth_headers)).status_code == 200
    # ...and rejected without it (a session is required — no silent bypass).
    assert (await client.get("/api/customers/")).status_code == 401

    # 3) Refresh issues a new, usable access token.
    refreshed = await client.post("/api/auth/refresh", headers=auth_headers)
    assert refreshed.status_code == 200
    new_token = refreshed.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}
    assert (await client.get("/api/auth/me", headers=new_headers)).status_code == 200

    # 4) Logout revokes the presented token (session invalidation is honoured).
    out = await client.post("/api/auth/logout", headers=new_headers)
    assert out.status_code == 200
    assert (await client.get("/api/auth/me", headers=new_headers)).status_code == 401


async def test_permission_enforcement(
    client: AsyncClient, auth_headers: dict, admin_headers: dict
):
    """Admin-only surfaces of the pipeline reject non-admin sessions.

    ``test_user`` is an *editor*: it can read its own data but must not reach
    the admin user-management API, which is guarded by ``require_admin``.
    """
    # Editor can read ordinary protected data.
    assert (await client.get("/api/customers/", headers=auth_headers)).status_code == 200
    # But the admin-only user-management surface is forbidden for the editor.
    assert (await client.get("/api/users/", headers=auth_headers)).status_code == 403
    # An admin session passes the same permission gate.
    assert (await client.get("/api/users/", headers=admin_headers)).status_code == 200


async def test_pipeline_handles_invalid_tokens_gracefully(client: AsyncClient):
    """Malformed/garbage credentials degrade to a clean 401, never a 500."""
    for bad in ("Bearer garbage-token", "Bearer ", "Token abc", "not-a-scheme"):
        resp = await client.get("/api/auth/me", headers={"Authorization": bad})
        assert resp.status_code == 401, f"{bad!r} -> {resp.status_code}"


async def test_facility_read_authorization_pipeline(client: AsyncClient, db_session):
    """Facility reads enforce explicit role-based authorization, not just auth.

    Resolves the logic-audit inconsistency between
    ``app/routers/facilities.py`` (authentication) and
    ``app/services/facility_authorization.py`` (authorization): an authenticated
    but *pending* account must be forbidden from facility data, while an approved
    (viewer/editor/admin) account may read it.
    """
    facilities_url = "/api/facilities/"

    # Unauthenticated → 401 (authentication still required, no silent bypass).
    assert (await client.get(facilities_url)).status_code == 401

    # Authenticated but pending → 403 (authenticated, not authorized).
    pending = await _make_user(db_session, "pending_fac", "pending")
    assert (await client.get(facilities_url, headers=_headers_for(pending))).status_code == 403

    # Approved viewer → 200, and read-only (cannot create).
    viewer = await _make_user(db_session, "viewer_fac", "viewer")
    assert (await client.get(facilities_url, headers=_headers_for(viewer))).status_code == 200
    create = await client.post(
        facilities_url,
        json={"customer_id": "nonexistent", "name": "X", "amount": 1000},
        headers=_headers_for(viewer),
    )
    assert create.status_code == 403  # require_editor blocks the viewer

    # Editor and admin can also read.
    editor = await _make_user(db_session, "editor_fac", "editor")
    assert (await client.get(facilities_url, headers=_headers_for(editor))).status_code == 200
    admin = await _make_user(db_session, "admin_fac", "admin")
    assert (await client.get(facilities_url, headers=_headers_for(admin))).status_code == 200
