"""Integration tests for login-endpoint rate limiting (brute-force guard).

Drives the real ``POST /api/auth/login`` route through the ASGI app and asserts
that repeated failed attempts from the same client are throttled with HTTP
``429 Too Many Requests`` once the per-minute limit is exceeded. The autouse
``_reset_security_state`` fixture in ``conftest.py`` clears the in-memory limiter
between tests, so the sequence is deterministic.
"""
import pytest
from httpx import AsyncClient

from app.config import settings


async def test_login_rate_limiting_too_many_requests(client: AsyncClient):
    """Five failed logins return 401; the next one is rejected with 429.

    The endpoint enforces ``LOGIN_RATE_LIMIT_PER_MINUTE`` (5) failed attempts per
    rolling 60-second window. Attempts 1..5 fail authentication normally (401);
    attempt 6 trips the throttle and is rejected with 429 *before* the
    credentials are checked, and the response advertises a ``Retry-After`` hint.
    """
    limit = settings.LOGIN_RATE_LIMIT_PER_MINUTE
    assert limit == 5

    statuses = []
    last_response = None
    for _ in range(limit + 1):
        last_response = await client.post(
            "/api/auth/login",
            data={"username": "brute-force-target", "password": "wrong-pass-1"},
        )
        statuses.append(last_response.status_code)

    # The first `limit` attempts are ordinary auth failures.
    assert statuses[:limit] == [401] * limit
    # The attempt that exceeds the limit is throttled.
    assert statuses[limit] == 429
    assert last_response is not None
    assert last_response.headers.get("Retry-After") == "60"
    # The throttle message must not leak credentials/internals.
    body = last_response.text.lower()
    assert "wrong-pass-1" not in body
    assert "too many" in body


async def test_rate_limit_is_per_client_key(client: AsyncClient):
    """Throttling one identifier does not throttle a different one."""
    limit = settings.LOGIN_RATE_LIMIT_PER_MINUTE

    # Exhaust the limit for user A.
    for _ in range(limit + 1):
        await client.post(
            "/api/auth/login",
            data={"username": "user-a", "password": "wrong-pass-1"},
        )

    # User A is now throttled.
    a_again = await client.post(
        "/api/auth/login",
        data={"username": "user-a", "password": "wrong-pass-1"},
    )
    assert a_again.status_code in (423, 429)

    # A different username (same client) still gets a normal 401, not a 429.
    b_first = await client.post(
        "/api/auth/login",
        data={"username": "user-b", "password": "wrong-pass-1"},
    )
    assert b_first.status_code == 401
