"""Integration tests for authentication.

Two complementary concerns live here:

1. Login status-code consistency (anti-enumeration): the login endpoint must
   return the **same** ``401 Unauthorized`` with the **same** generic message
   whether the supplied username does not exist or the password is simply wrong.
   Diverging status codes or messages would let an attacker enumerate valid
   usernames. This holds for both supported request encodings (OAuth2 form post
   and JSON body).

2. The JWT creation/validation contract that spans the ``app.utils.security``
   <-> ``app.config`` boundary: ``create_access_token`` embeds the standard
   ``iss`` / ``aud`` claims sourced from ``Settings.JWT_ISSUER`` /
   ``Settings.JWT_AUDIENCE``, and ``verify_access_token`` validates those same
   claims against the configured values, so a drift between config and security
   (e.g. a missing ``JWT_ISSUER`` attribute) is caught.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from jose import jwt

from app.config import settings
from app.models.user import User
from app.utils.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    verify_access_token,
)

_GENERIC_LOGIN_ERROR = "Incorrect username or password"


async def test_login_status_codes_prevent_enumeration(
    client: AsyncClient, test_user: User
):
    """A non-existent user and a wrong password are indistinguishable to a client.

    Both cases must yield identical (status_code, detail) pairs so the response
    leaks nothing about whether an account exists.
    """
    # Case A: the username does not exist at all.
    nonexistent = await client.post(
        "/api/auth/login",
        data={"username": "no-such-user", "password": "whatever123"},
    )

    # Case B: the username exists but the password is wrong.
    wrong_password = await client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "definitely-wrong"},
    )

    # Identical status codes...
    assert nonexistent.status_code == 401
    assert wrong_password.status_code == 401
    assert nonexistent.status_code == wrong_password.status_code

    # ...and identical, generic error messages — no enumeration signal.
    assert nonexistent.json()["detail"] == _GENERIC_LOGIN_ERROR
    assert wrong_password.json()["detail"] == _GENERIC_LOGIN_ERROR
    assert nonexistent.json()["detail"] == wrong_password.json()["detail"]


async def test_login_json_body_bad_credentials_returns_401(client: AsyncClient):
    """A JSON login with bad credentials returns 401 (not 422).

    The endpoint accepts a JSON body of ``{"email"|"username", "password"}`` in
    addition to the OAuth2 form post. Bad credentials supplied as JSON must fail
    authentication (401) rather than being rejected as malformed input (422), so
    JSON clients get the same anti-enumeration behaviour as form clients.
    """
    resp = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "anypassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == _GENERIC_LOGIN_ERROR


async def test_login_form_and_json_paths_agree(
    client: AsyncClient, test_user: User
):
    """Valid credentials authenticate identically via form and JSON encodings."""
    form_login = await client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "testpass123"},
    )
    assert form_login.status_code == 200
    assert "access_token" in form_login.json()

    json_login = await client.post(
        "/api/auth/login",
        json={"username": test_user.username, "password": "testpass123"},
    )
    assert json_login.status_code == 200
    assert "access_token" in json_login.json()


def test_jwt_token_creation_and_validation():
    # config must expose the claims that security.py relies on.
    assert settings.JWT_ISSUER
    assert settings.JWT_AUDIENCE

    token = create_access_token({"user_id": "u-123", "username": "alice"})

    # Round-trip: a freshly minted token validates and carries the standard
    # issuer/audience claims taken from config.
    payload = verify_access_token(token)
    assert payload["user_id"] == "u-123"
    assert payload["username"] == "alice"
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert payload["type"] == "access"

    # A token whose issuer disagrees with config must be rejected, proving the
    # validation actually consults the configured JWT_ISSUER value. The audience
    # is left correct so the issuer check is what trips.
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {
            "user_id": "u-123",
            "username": "alice",
            "type": "access",
            "iss": "evil-issuer",
            "aud": settings.JWT_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc:
        verify_access_token(forged)
    assert exc.value.status_code == 401
    assert "issuer" in exc.value.detail.lower()
