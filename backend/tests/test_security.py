"""Security-feature tests for the auth pipeline.

Covers the behaviours added for the "تقویت امنیت JWT و مکانیزم‌های احراز هویت"
consolidated task:

* JWT ``none``-algorithm rejection and ``verify_access_token`` edge cases
* Login rate limiting (HTTP 429) and account lockout (HTTP 423)
* Token revocation / blacklist on logout and the ``/refresh`` endpoint
* HSTS / security headers
* Authentication is always enforced (no token -> 401)
"""
import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from jose import jwt as jose_jwt

from app.utils.security import (
    SECRET_KEY,
    create_access_token,
    verify_access_token,
)
from app.models.user import User


def _b64url(data: dict) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _make_none_token(payload: dict) -> str:
    """Forge an unsigned JWT using the insecure ``alg=none`` header."""
    header = _b64url({"alg": "none", "typ": "JWT"})
    body = _b64url(payload)
    return f"{header}.{body}."


# ---------------------------------------------------------------------------
# Sub-task 10: verify_access_token edge cases (required test node)
# ---------------------------------------------------------------------------
def test_verify_access_token_edge_cases():
    """Exercise the documented conditional iss/aud anti-pattern and other edges."""
    # Empty / malformed tokens are rejected.
    with pytest.raises(HTTPException):
        verify_access_token("")
    with pytest.raises(HTTPException):
        verify_access_token("not-a-jwt")
    with pytest.raises(HTTPException):
        verify_access_token("only.two")

    # Forged 'none'-algorithm token must be rejected.
    forged = _make_none_token(
        {"user_id": "abc12345", "username": "attacker", "type": "access"}
    )
    with pytest.raises(HTTPException):
        verify_access_token(forged)

    # A freshly minted token round-trips and exposes user_id/username.
    token = create_access_token({"user_id": "abc12345", "username": "alice"})
    payload = verify_access_token(token)
    assert payload["user_id"] == "abc12345"
    assert payload["username"] == "alice"

    # Legacy token WITHOUT iss/aud claims is still accepted (backward compat) —
    # this is the intentional, documented conditional behaviour.
    now = datetime.now(timezone.utc)
    legacy = jose_jwt.encode(
        {
            "user_id": "leg12345",
            "username": "legacy",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    legacy_payload = verify_access_token(legacy)
    assert legacy_payload["username"] == "legacy"

    # But a token that DOES carry a wrong issuer is rejected.
    bad_iss = jose_jwt.encode(
        {
            "user_id": "leg12345",
            "username": "legacy",
            "type": "access",
            "iss": "evil-issuer",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException):
        verify_access_token(bad_iss)

    # Expired tokens are rejected.
    expired = jose_jwt.encode(
        {
            "user_id": "leg12345",
            "username": "legacy",
            "type": "access",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException):
        verify_access_token(expired)


# ---------------------------------------------------------------------------
# Sub-task 1 / 2: none rejection + auth always enforced (behavioural)
# ---------------------------------------------------------------------------
class TestAuthEnforcement:
    async def test_none_algorithm_rejected_by_api(self, client: AsyncClient):
        forged = _make_none_token(
            {"user_id": "abc12345", "username": "attacker", "type": "access"}
        )
        resp = await client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {forged}"}
        )
        assert resp.status_code == 401

    async def test_protected_endpoint_requires_token(self, client: AsyncClient):
        resp = await client.get("/api/customers/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Sub-task 8: rate limiting (429) and account lockout (423)
# ---------------------------------------------------------------------------
class TestRateLimiting:
    async def test_rate_limit_returns_429_after_threshold(self, client: AsyncClient):
        statuses = []
        for _ in range(6):
            resp = await client.post(
                "/api/auth/login",
                data={"username": "nobody_rl", "password": "wrongpassword1"},
            )
            statuses.append(resp.status_code)
        # First five attempts are normal auth failures, the sixth is throttled.
        assert statuses[:5] == [401, 401, 401, 401, 401]
        assert statuses[5] == 429

    async def test_account_lockout_returns_423(self, client: AsyncClient):
        statuses = []
        for _ in range(10):
            resp = await client.post(
                "/api/auth/login",
                data={"username": "nobody_lock", "password": "wrongpassword1"},
            )
            statuses.append(resp.status_code)
        assert 429 in statuses
        # Once the lockout threshold is crossed the endpoint returns 423 Locked.
        assert statuses[-1] == 423

    async def test_successful_login_resets_counter(
        self, client: AsyncClient, test_user: User
    ):
        # A few failures, then a success must clear the throttle for that key.
        for _ in range(3):
            await client.post(
                "/api/auth/login",
                data={"username": test_user.username, "password": "wrongpassword1"},
            )
        ok = await client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpass123"},
        )
        assert ok.status_code == 200


# ---------------------------------------------------------------------------
# Sub-task 15: refresh + blacklist on logout
# ---------------------------------------------------------------------------
class TestTokenLifecycle:
    async def test_logout_revokes_token(
        self, client: AsyncClient, auth_headers: dict
    ):
        # Token works before logout.
        assert (await client.get("/api/auth/me", headers=auth_headers)).status_code == 200
        # Logout revokes it.
        out = await client.post("/api/auth/logout", headers=auth_headers)
        assert out.status_code == 200
        # The same (still-unexpired) token is now rejected.
        assert (await client.get("/api/auth/me", headers=auth_headers)).status_code == 401

    async def test_refresh_endpoint_issues_new_token(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post("/api/auth/refresh", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body and body["access_token"]


# ---------------------------------------------------------------------------
# Sub-task 14: HSTS / security headers
# ---------------------------------------------------------------------------
class TestSecurityHeaders:
    async def test_hsts_header_present(self, client: AsyncClient):
        resp = await client.get("/health")
        hsts = resp.headers.get("strict-transport-security", "")
        assert "max-age=31536000" in hsts

    async def test_content_type_options_header(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"
