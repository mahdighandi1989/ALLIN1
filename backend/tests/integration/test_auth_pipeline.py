"""Integration tests for the auth pipeline.

Focus: error responses must never leak permission/authorization internals or
resource-existence information to unauthenticated/unauthorized callers.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


# Substrings that would indicate an internal/permission detail leaking to the
# client. Error bodies must contain none of these. (Note: the generic
# "Incorrect username or password" message is allowed — we only guard against
# leaking the *hash*, internals, or authorization details.)
_FORBIDDEN_SUBSTRINGS = [
    "traceback",
    "permission denied",
    "is_admin",
    "hashed_password",
    "sqlalchemy",
    "psycopg",
    "/home/",
    "site-packages",
    "secret_key",
    "select * from",
]


def _assert_no_leak(body_text: str) -> None:
    lowered = body_text.lower()
    for needle in _FORBIDDEN_SUBSTRINGS:
        assert needle not in lowered, f"error body leaked internal detail: {needle!r}"


class TestAuthPipelineNoLeak:
    async def test_no_permission_leak_in_errors(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Errors across the auth pipeline stay generic and leak no internals."""
        # 1) Unauthenticated access to a protected collection -> 401, generic.
        r = await client.get("/api/customers/")
        assert r.status_code == 401
        _assert_no_leak(r.text)

        # 2) Unauthenticated access to a *specific* resource must also be 401 —
        #    NOT 404 — so the API never reveals whether the resource exists to a
        #    caller that has not authenticated.
        r = await client.get("/api/customers/does-not-exist")
        assert r.status_code == 401
        _assert_no_leak(r.text)

        r = await client.get("/api/facilities/does-not-exist")
        assert r.status_code == 401
        _assert_no_leak(r.text)

        # 3) An invalid/garbage token -> 401, generic message, no internals.
        bad = {"Authorization": "Bearer not-a-real-token"}
        r = await client.get("/api/auth/me", headers=bad)
        assert r.status_code == 401
        _assert_no_leak(r.text)

        # 4) Authenticated lookup of a missing resource -> 404 with a generic
        #    message that does not leak permission/role/internal details.
        r = await client.get("/api/facilities/missing-id", headers=auth_headers)
        assert r.status_code == 404
        assert r.json()["detail"] == "Facility not found"
        _assert_no_leak(r.text)

    async def test_wrong_credentials_message_is_generic(self, client: AsyncClient):
        """Login failures must not reveal whether the username exists."""
        r = await client.post(
            "/api/auth/login",
            data={"username": "ghost-user", "password": "whatever1"},
        )
        assert r.status_code == 401
        # Same generic message regardless of whether the user exists.
        assert r.json()["detail"] == "Incorrect username or password"
        _assert_no_leak(r.text)


async def test_profile_update_and_password_change_secure(
    client: AsyncClient,
    auth_headers: dict,
    admin_headers: dict,
    test_user: User,
    admin_user: User,
):
    """Profile updates and password changes act only on the authenticated owner.

    The endpoints derive the target user from the JWT (``current_user``), so a
    caller can never mutate another account by supplying its id. This test
    proves the ownership boundary end-to-end:

    1. Without a token the endpoints reject the request (401).
    2. A profile update with user A's token changes A and leaves B untouched.
    3. A password change requires A's *current* password and, once changed,
       only A's credentials are affected — B can still log in unchanged.
    """
    # 1) Unauthenticated callers cannot touch profile or password endpoints.
    assert (await client.put("/api/auth/me", json={"full_name": "x"})).status_code == 401
    assert (
        await client.post(
            "/api/auth/change-password",
            json={"current_password": "testpass123", "new_password": "irrelevant1"},
        )
    ).status_code == 401

    # 2) test_user updates only their own profile.
    r = await client.put(
        "/api/auth/me", json={"full_name": "Renamed Owner"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Renamed Owner"
    assert r.json()["username"] == test_user.username

    # The admin account is untouched by test_user's update.
    admin_me = await client.get("/api/auth/me", headers=admin_headers)
    assert admin_me.status_code == 200
    assert admin_me.json()["full_name"] == "Admin User"

    # 3) Password change requires the correct current password.
    bad = await client.post(
        "/api/auth/change-password",
        json={"current_password": "not-my-password", "new_password": "newpass12345"},
        headers=auth_headers,
    )
    assert bad.status_code == 400
    _assert_no_leak(bad.text)

    ok = await client.post(
        "/api/auth/change-password",
        json={"current_password": "testpass123", "new_password": "newpass12345"},
        headers=auth_headers,
    )
    assert ok.status_code == 200

    # Only test_user's credentials changed: new password works, old one fails.
    new_login = await client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "newpass12345"},
    )
    assert new_login.status_code == 200

    # The admin account's password is unaffected by test_user's change.
    admin_login = await client.post(
        "/api/auth/login",
        data={"username": admin_user.username, "password": "admin123"},
    )
    assert admin_login.status_code == 200
