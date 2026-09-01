"""Google OAuth 2.0 (Authorization Code flow) helpers.

Server-side flow so it works with the static-export frontend AND yields an
offline refresh token (needed for the Drive backup). All network calls go
through httpx; nothing here touches the DB.
"""
from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# openid/email/profile for login; drive.file lets us create + write only the
# backup files we own (least privilege — we can't read the user's other files).
LOGIN_SCOPES = ["openid", "email", "profile"]
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
DEFAULT_SCOPES = LOGIN_SCOPES + [DRIVE_SCOPE]


class GoogleOAuthError(Exception):
    """Raised when a Google OAuth/token/userinfo call fails."""


def build_auth_url(
    state: str, *, redirect_uri: str | None = None, include_drive: bool = True
) -> str:
    """Build the Google consent-screen URL to redirect the browser to.

    ``redirect_uri`` defaults to ``settings.GOOGLE_REDIRECT_URI`` but can be
    passed explicitly (the caller derives it from the request when the setting is
    blank) so the same value is used here and in :func:`exchange_code`.
    """
    scopes = DEFAULT_SCOPES if include_drive else LOGIN_SCOPES
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri or settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "access_type": "offline",     # ask for a refresh token (for backups)
        "prompt": "consent",          # ensure a refresh token is returned
    }
    # v115 — include_granted_scopes=true made Google MERGE every scope the user
    # ever granted this client_id into our request; the owner's account carried
    # YouTube grants (another tool reuses the client) and Google now refuses
    # drive.file + YouTube scopes in one request ⇒ «Access blocked: Error 400»
    # on every login. We request everything we need each time, so incremental
    # authorization buys us nothing — off by default, old behavior kept behind
    # the flag for rollback.
    if settings.GOOGLE_INCLUDE_GRANTED_SCOPES:
        params["include_granted_scopes"] = "true"
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str, redirect_uri: str | None = None) -> dict:
    """Exchange an authorization code for tokens (access/refresh/id_token).

    ``redirect_uri`` MUST match the value used to build the consent URL, so the
    caller passes the same derived/explicit value it gave :func:`build_auth_url`.
    """
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri or settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise GoogleOAuthError(f"token exchange failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Mint a fresh access token from a stored refresh token (for backups)."""
    data = {
        "refresh_token": refresh_token,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise GoogleOAuthError(f"token refresh failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


async def fetch_userinfo(access_token: str) -> dict:
    """Fetch the signed-in user's profile (sub, email, name, picture)."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
    if resp.status_code != 200:
        raise GoogleOAuthError(f"userinfo failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()
