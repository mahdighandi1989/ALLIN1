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
from app.utils.security import create_access_token, hash_password
from app.services.google_oauth import (
    GoogleOAuthError,
    build_auth_url,
    exchange_code,
    fetch_userinfo,
)

logger = logging.getLogger("app.google_auth")
router = APIRouter(tags=["google-auth"])

_STATE_COOKIE = "g_oauth_state"


def _frontend_redirect(path_with_query: str) -> RedirectResponse:
    # Relative redirect — the SPA is served from the same origin as the API.
    return RedirectResponse(url=path_with_query, status_code=status.HTTP_302_FOUND)


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
async def google_login():
    """Redirect the browser to Google's consent screen."""
    if not settings.google_oauth_configured():
        return _frontend_redirect("/login?error=google_not_configured")
    state = secrets.token_urlsafe(24)
    resp = _frontend_redirect(build_auth_url(state))
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
        tokens = await exchange_code(code)
        info = await fetch_userinfo(tokens["access_token"])
    except (GoogleOAuthError, KeyError) as exc:
        logger.warning("google oauth callback failed: %s", exc)
        return _frontend_redirect("/login?error=google_auth_failed")

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
