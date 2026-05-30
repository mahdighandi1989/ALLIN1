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
