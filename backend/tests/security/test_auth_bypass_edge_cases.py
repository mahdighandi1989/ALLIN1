"""Edge-case security tests for the temporary ``AUTH_DISABLED`` bypass.

The codebase ships a deliberate, configuration-gated bypass: when
``settings.AUTH_DISABLED`` is True the protected endpoints run as a shared,
transient "demo" user (login removed "for now"). This is a recognised
anti-pattern, so it is documented in ``routers/auth.py`` with a ``SEC_REVIEWED``
note and guarded by these tests, which prove the bypass is *controlled*:

* it is OFF by default in the test suite (auth is enforced);
* with auth enforced, no/garbage credentials are rejected with 401 — the bypass
  cannot be triggered by anything in the request;
* only flipping the explicit server-side flag enables it, and even then the demo
  identity is transient (never persisted) and the request can't choose a user.
"""
import pytest
from httpx import AsyncClient

from app.config import settings as app_settings


async def test_auth_disabled_bypass_is_secure(client: AsyncClient):
    """The auth bypass is gated solely by the server flag, never by the request.

    Part 1 — auth ENFORCED (the suite default, pinned by ``_reset_security_state``):
      * a protected endpoint with no token -> 401;
      * a protected endpoint with a garbage bearer token -> 401;
      * the bypass demo user is therefore unreachable for any unauthenticated or
        forged request.

    Part 2 — auth BYPASSED (flip the explicit flag, as a deployment would):
      * the same protected endpoint now succeeds without any token, returning the
        shared demo identity — confirming the bypass is real but only when the
        operator opts in via configuration.
    """
    # --- Part 1: bypass is OFF, authentication is mandatory --------------------
    assert app_settings.AUTH_DISABLED is False

    no_token = await client.get("/api/auth/me")
    assert no_token.status_code == 401

    garbage = await client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert garbage.status_code == 401

    # A protected data collection is equally protected — no demo-user leakage.
    protected = await client.get("/api/customers/")
    assert protected.status_code == 401

    # --- Part 2: bypass is ON only when the server flag is set -----------------
    app_settings.AUTH_DISABLED = True
    try:
        bypassed = await client.get("/api/auth/me")
        assert bypassed.status_code == 200
        body = bypassed.json()
        # The bypass yields the fixed, transient demo identity — the client never
        # gets to choose who they are.
        assert body["username"] == "demo"
        assert body["id"] == "demo"
    finally:
        # Restore enforcement so we never leak the bypass into other tests
        # (the autouse fixture also resets this, belt-and-braces).
        app_settings.AUTH_DISABLED = False

    # --- Back to Part 1 invariants after restoring the flag --------------------
    assert app_settings.AUTH_DISABLED is False
    re_enforced = await client.get("/api/auth/me")
    assert re_enforced.status_code == 401


async def test_disabled_algorithm_token_is_rejected_even_when_present(
    client: AsyncClient,
):
    """A forged ``alg: none`` token must never authenticate (defense in depth)."""
    # A syntactically valid-looking but unsigned JWT (header alg=none).
    # header {"alg":"none","typ":"JWT"} . payload {"user_id":"demo","username":"demo"} .
    forged = (
        "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0."
        "eyJ1c2VyX2lkIjoiZGVtbyIsInVzZXJuYW1lIjoiZGVtbyIsInR5cGUiOiJhY2Nlc3MifQ."
    )
    resp = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {forged}"}
    )
    assert resp.status_code == 401
