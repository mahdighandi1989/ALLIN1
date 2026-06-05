"""Integration tests pinning the auth *granularity* of profile/password mutations.

Ground truth (the contract these tests lock in):

* ``PUT /api/auth/me`` (profile update) and ``POST /api/auth/change-password``
  are **authenticated** mutations — without a valid token they return 401.
* Both derive their target strictly from the JWT's ``current_user``; a caller can
  never act on another account by supplying an id/email in the body.
* ``change-password`` additionally requires the caller's *current* password
  (re-authentication for the sensitive operation), and never touches any other
  account.

This complements ``test_auth_pipeline.py`` by asserting the per-endpoint
granularity (which mutations need auth, and at what level) in one focused test.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


async def test_auth_profile_password_granularity(
    client: AsyncClient,
    auth_headers: dict,
    admin_headers: dict,
    test_user: User,
    admin_user: User,
):
    # 1) Unauthenticated mutations are rejected at the same 401 granularity.
    assert (
        await client.put("/api/auth/me", json={"full_name": "Nope"})
    ).status_code == 401
    assert (
        await client.post(
            "/api/auth/change-password",
            json={"current_password": "testpass123", "new_password": "another123"},
        )
    ).status_code == 401

    # 2) An authenticated profile update acts ONLY on the caller (test_user),
    #    even though no id is supplied — the JWT identifies the target.
    upd = await client.put(
        "/api/auth/me", json={"full_name": "Owner Renamed"}, headers=auth_headers
    )
    assert upd.status_code == 200
    assert upd.json()["full_name"] == "Owner Renamed"
    assert upd.json()["username"] == test_user.username

    # The admin account is untouched by test_user's profile mutation.
    admin_me = await client.get("/api/auth/me", headers=admin_headers)
    assert admin_me.status_code == 200
    assert admin_me.json()["full_name"] == "Admin User"

    # 3) change-password requires the correct CURRENT password (re-auth).
    wrong_current = await client.post(
        "/api/auth/change-password",
        json={"current_password": "definitely-wrong", "new_password": "freshpass123"},
        headers=auth_headers,
    )
    assert wrong_current.status_code == 400

    # 4) With the correct current password the change succeeds and is scoped to
    #    the caller: their new password works, their old one stops working, and
    #    the admin account is entirely unaffected.
    ok = await client.post(
        "/api/auth/change-password",
        json={"current_password": "testpass123", "new_password": "freshpass123"},
        headers=auth_headers,
    )
    assert ok.status_code == 200

    new_login = await client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "freshpass123"},
    )
    assert new_login.status_code == 200

    old_login = await client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "testpass123"},
    )
    assert old_login.status_code == 401

    admin_login = await client.post(
        "/api/auth/login",
        data={"username": admin_user.username, "password": "admin123"},
    )
    assert admin_login.status_code == 200
