"""Google Sign-In endpoints (wired at /api/auth/google).

GET /login    -> redirect the browser to Google's consent screen.
GET /callback -> Google redirects back here with a code; we exchange it, create
                 or update the user, issue our app JWT, and redirect to the SPA.

New users are created with role 'pending' (no access until an admin grants a
role) — except emails listed in settings.ADMIN_EMAILS, which are always admins.
"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, ROLE_ADMIN, ROLE_PENDING
from app.utils.security import create_access_token, hash_password, verify_access_token
from app.routers.auth import require_admin
from app.services.google_oauth import (
    GoogleOAuthError,
    build_auth_url,
    exchange_code,
    fetch_userinfo,
)

logger = logging.getLogger("app.google_auth")
router = APIRouter(tags=["google-auth"])

_STATE_COOKIE = "g_oauth_state"
# A state value prefixed with this marks the OAuth round-trip as a "connect Drive"
# flow rather than a login, so the shared callback stores the refresh token for
# Drive sync instead of issuing an app session. Reusing the login callback means
# no extra Authorized redirect URI has to be registered in the Google console.
_DRIVE_STATE_PREFIX = "drive:"


def _effective_redirect_uri(request: Request) -> str:
    """The OAuth redirect URI to use for this flow.

    Prefers the explicit ``GOOGLE_REDIRECT_URI`` setting; when it is blank the
    URI is derived from the incoming request so Google Sign-In works out of the
    box on Render with only the client id/secret set. ``X-Forwarded-Proto`` /
    ``X-Forwarded-Host`` are honoured so the derived URI is the public https URL
    (uvicorn sees plain http behind Render's TLS-terminating proxy).

    The browser is redirected to ``/api/auth/google/callback`` on the same host
    for both the consent URL and the token exchange, so the two values always
    match (a hard Google requirement).
    """
    if settings.GOOGLE_REDIRECT_URI:
        return settings.GOOGLE_REDIRECT_URI
    proto = (
        request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    ).split(",")[0].strip()
    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.netloc
    ).split(",")[0].strip()
    return f"{proto}://{host}/api/auth/google/callback"


def _frontend_redirect(
    path_with_query: str, status_code: int = status.HTTP_302_FOUND
) -> RedirectResponse:
    # Relative redirect — the SPA is served from the same origin as the API.
    return RedirectResponse(url=path_with_query, status_code=status_code)


async def _unique_username(db: AsyncSession, email: str) -> str:
    base = (email.split("@", 1)[0] or "user").lower()
    base = "".join(ch for ch in base if ch.isalnum() or ch in "._-")[:40] or "user"
    candidate = base
    n = 0
    while True:
        exists = (await db.execute(select(User.id).where(User.username == candidate))).scalar_one_or_none()
        if not exists:
            return candidate
        n += 1
        candidate = f"{base}{n}"[:50]


async def upsert_google_user(db: AsyncSession, info: dict, tokens: dict) -> User:
    """Create or update the local user for this Google identity."""
    sub = str(info.get("sub") or "").strip()
    email = str(info.get("email") or "").strip().lower()
    name = info.get("name") or info.get("given_name") or (email.split("@", 1)[0] if email else "")
    picture = info.get("picture")
    refresh_token = tokens.get("refresh_token")
    admin_emails = settings.get_admin_emails()

    # Match an existing account by google_sub first, then by email.
    user = None
    if sub:
        user = (await db.execute(select(User).where(User.google_sub == sub))).scalar_one_or_none()
    if user is None and email:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

    if user is None:
        user = User(
            username=await _unique_username(db, email or sub or "user"),
            email=email or f"{sub}@google.local",
            hashed_password=hash_password(secrets.token_urlsafe(32)),  # no password login
            full_name=name,
            is_active=True,
            auth_provider="google",
            google_sub=sub or None,
            picture=picture,
            role=ROLE_ADMIN if email in admin_emails else ROLE_PENDING,
        )
        if email in admin_emails:
            user.is_admin = True
        db.add(user)
    else:
        # Update profile + link the Google identity.
        user.auth_provider = "google"
        if sub:
            user.google_sub = sub
        if picture:
            user.picture = picture
        if name and not user.full_name:
            user.full_name = name
        if email in admin_emails:
            user.role = ROLE_ADMIN
            user.is_admin = True

    # Persist the refresh token so the same account can drive Drive backups.
    if refresh_token:
        user.google_refresh_token = refresh_token
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/login")
async def google_login(request: Request):
    """Redirect the browser to Google's consent screen.

    Uses a 307 (Temporary Redirect) so the redirect is an explicit, method-
    preserving hand-off to Google's OAuth authorization URL.
    """
    if not settings.google_oauth_configured():
        return _frontend_redirect(
            "/login?error=google_not_configured", status.HTTP_307_TEMPORARY_REDIRECT
        )
    state = secrets.token_urlsafe(24)
    redirect_uri = _effective_redirect_uri(request)
    resp = _frontend_redirect(
        build_auth_url(state, redirect_uri=redirect_uri),
        status.HTTP_307_TEMPORARY_REDIRECT,
    )
    resp.set_cookie(
        _STATE_COOKIE, state, max_age=600, httponly=True,
        secure=settings.is_production(), samesite="lax", path="/",
    )
    return resp


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google's redirect: exchange code, upsert user, issue our JWT."""
    if error:
        return _frontend_redirect(f"/login?error={error}")
    if not code:
        return _frontend_redirect("/login?error=missing_code")
    # CSRF: the state in the query must match the one we set in the cookie.
    cookie_state = request.cookies.get(_STATE_COOKIE)
    if not state or not cookie_state or state != cookie_state:
        return _frontend_redirect("/login?error=state_mismatch")

    try:
        tokens = await exchange_code(code, _effective_redirect_uri(request))
        info = await fetch_userinfo(tokens["access_token"])
    except (GoogleOAuthError, KeyError) as exc:
        logger.warning("google oauth callback failed: %s", exc)
        return _frontend_redirect("/login?error=google_auth_failed")

    # "Connect Google Drive" flow: store the refresh token for Drive sync and go
    # back to Settings — no app session is issued here (the admin is already
    # logged in). Detected by the state prefix set in /drive/connect.
    if state.startswith(_DRIVE_STATE_PREFIX):
        from app.services import drive_settings

        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            # Without a refresh token we can't sync later; ask Google to re-consent.
            resp = _frontend_redirect("/settings?drive=error_no_refresh_token")
            resp.delete_cookie(_STATE_COOKIE, path="/")
            return resp
        await drive_settings.store_connection(refresh_token, info.get("email"))
        logger.info("Google Drive connected for sync: %s", info.get("email"))
        resp = _frontend_redirect("/settings?drive=connected")
        resp.delete_cookie(_STATE_COOKIE, path="/")
        return resp

    user = await upsert_google_user(db, info, tokens)

    try:
        from app.services.audit import record_audit
        await record_audit(
            action="login", entity_type="auth", entity_id=user.id,
            detail=f"Google sign-in: {user.email}", user=user, request=request, db=db,
        )
    except Exception:  # auditing must never block login
        pass

    app_token = create_access_token(
        data={"user_id": user.id, "username": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    query = urlencode({"token": app_token, "role": user.role})
    resp = _frontend_redirect(f"{settings.POST_LOGIN_REDIRECT_PATH}?{query}")
    resp.delete_cookie(_STATE_COOKIE, path="/")
    return resp


async def _require_admin_from_query_token(token: str, db: AsyncSession) -> User | None:
    """Validate an admin JWT passed as a query param (top-level navigations can't
    send an Authorization header). Returns the admin user or None."""
    if not token:
        return None
    try:
        payload = verify_access_token(token)
    except Exception:
        return None
    user = (
        await db.execute(select(User).where(User.id == payload.get("user_id")))
    ).scalar_one_or_none()
    if user and (user.is_admin or user.role == ROLE_ADMIN):
        return user
    return None


@router.get("/drive/connect")
async def drive_connect(request: Request, token: str = "", db: AsyncSession = Depends(get_db)):
    """Start the one-time 'Connect Google Drive' consent (admin only).

    The admin JWT is passed as ``?token=`` because this is a top-level browser
    navigation (no Authorization header). On success the browser is sent to
    Google's consent screen with ``access_type=offline`` so we receive a refresh
    token, which the shared callback stores for Drive sync.
    """
    if not settings.google_oauth_configured():
        return _frontend_redirect("/settings?drive=google_not_configured")
    admin = await _require_admin_from_query_token(token, db)
    if admin is None:
        return _frontend_redirect("/settings?drive=forbidden")

    state = _DRIVE_STATE_PREFIX + secrets.token_urlsafe(24)
    redirect_uri = _effective_redirect_uri(request)
    resp = _frontend_redirect(
        build_auth_url(state, redirect_uri=redirect_uri, include_drive=True),
        status.HTTP_307_TEMPORARY_REDIRECT,
    )
    resp.set_cookie(
        _STATE_COOKIE, state, max_age=600, httponly=True,
        secure=settings.is_production(), samesite="lax", path="/",
    )
    return resp


@router.post("/drive/disconnect")
async def drive_disconnect(user=Depends(require_admin)):
    """Forget the stored Drive refresh token (admin only)."""
    from app.services import drive_settings

    await drive_settings.clear_setting(drive_settings.REFRESH_TOKEN_KEY)
    await drive_settings.clear_setting(drive_settings.ACCOUNT_KEY)
    return {"ok": True, "disconnected": True}
