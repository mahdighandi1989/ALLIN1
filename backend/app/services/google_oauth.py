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


def build_auth_url(state: str, *, include_drive: bool = True) -> str:
    """Build the Google consent-screen URL to redirect the browser to."""
    scopes = DEFAULT_SCOPES if include_drive else LOGIN_SCOPES
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "access_type": "offline",     # ask for a refresh token (for backups)
        "include_granted_scopes": "true",
        "prompt": "consent",          # ensure a refresh token is returned
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    """Exchange an authorization code for tokens (access/refresh/id_token)."""
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
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
