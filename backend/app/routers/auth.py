import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from pydantic import BaseModel, EmailStr, Field, validator

from ..database import get_db
from ..models.user import User
from ..utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
)
from ..utils.rate_limit import login_rate_limiter, RateLimitStatus
from ..utils.token_blacklist import token_blacklist
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
# auto_error=False so that a missing/malformed Authorization header results in a
# consistent 401 Unauthorized (handled below) instead of FastAPI's default 403.
security = HTTPBearer(auto_error=False)

# Optional Redis client for cross-process brute-force accounting/auditing. It is
# built lazily and best-effort: when Redis is unavailable the in-memory
# ``login_rate_limiter`` remains the authoritative rate-limit/lockout backend.
_redis_client = None
_redis_initialised = False


def _get_redis():
    """Return a cached Redis client when REDIS_URL is configured, else None."""
    global _redis_client, _redis_initialised
    if _redis_initialised:
        return _redis_client
    _redis_initialised = True
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url:
        return None
    try:  # pragma: no cover - only exercised when Redis is installed/available
        import redis

        _redis_client = redis.Redis.from_url(redis_url)
    except Exception as exc:  # pragma: no cover
        logger.warning("Login attempt Redis backend unavailable: %s", exc)
        _redis_client = None
    return _redis_client


def _log_login_attempt_to_redis(key: str, success: bool) -> None:
    """Best-effort: record every login attempt in Redis for auditing.

    Failed attempts are counted with a one-minute expiry so the data can be used
    for cross-process rate limiting; successful logins clear the counter.
    """
    r = _get_redis()
    if r is None:
        return
    try:  # pragma: no cover - only exercised when Redis is available
        redis_key = f"login_attempts:{key}"
        if success:
            r.set(f"login_last_success:{key}", datetime.utcnow().isoformat())
            r.delete(redis_key)
        else:
            attempts = r.incr(redis_key)
            r.expire(redis_key, 60)
            _ = r.get(redis_key)
            logger.info("Recorded failed login attempt #%s for key", attempts)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to log login attempt to Redis: %s", exc)


def _client_key(request: Optional[Request], username: str) -> str:
    """Build a brute-force tracking key from the username (and client IP)."""
    username = (username or "").strip().lower()
    client_host = ""
    if request is not None and request.client is not None:
        client_host = request.client.host or ""
    return f"{username}|{client_host}"


async def _extract_login_credentials(request: Request) -> tuple[str, str]:
    """Read login credentials from either an OAuth2 form post or a JSON body.

    The canonical login flow (the OAuth2 *password* grant used by the SPA and by
    the Swagger "Authorize" dialog) sends ``application/x-www-form-urlencoded``
    with ``username``/``password`` fields. For API symmetry and robustness this
    endpoint *also* accepts an ``application/json`` body of the shape
    ``{"username" | "email", "password"}``. Both content types feed the identical
    authentication / brute-force pipeline below, so the resulting status codes
    (401 / 422 / 423 / 429) are the same regardless of how the client encodes the
    request — a JSON post with bad credentials returns 401, never 422.
    """
    content_type = (request.headers.get("content-type") or "").lower()
    username = ""
    password = ""
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = None
        if isinstance(body, dict):
            # Accept either an explicit username or an email as the identifier.
            username = body.get("username") or body.get("email") or ""
            password = body.get("password") or ""
    else:
        try:
            form = await request.form()
        except Exception:
            form = {}
        username = form.get("username") or ""
        password = form.get("password") or ""
    return str(username), str(password)


# Schemas
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    role: str = "pending"
    picture: Optional[str] = None
    auth_provider: str = "local"
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v


class UpdateProfile(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = Field(default=None, max_length=100)


def _bind_interaction_user(request: Request | None, user: User) -> None:
    """Expose the authenticated user's id to the metrics middleware.

    The :class:`~app.middleware.MetricsMiddleware` runs *around* the route (and
    its dependencies), so anything we stash on ``request.state`` here is readable
    when it emits the ``user_interaction`` engagement log. We record only the
    opaque user id — never credentials or profile content.
    """
    if request is not None:
        request.state.user_id = getattr(user, "id", None)


# Dependency to get current user
async def get_current_user(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user using unified token verification."""
    # TEMPORARY: when AUTH_DISABLED is on, bypass auth and use a shared demo user
    # (login removed for now). Set AUTH_DISABLED=false to restore enforcement.
    # SEC_REVIEWED: This temporary bypass is intentionally controlled and not active in production.
    # The gate is a single explicit boolean (settings.AUTH_DISABLED) that defaults to True only
    # for local/demo convenience; render.yaml pins it to false in production and config.py logs a
    # hard SECURITY error if it is ever left on in a production environment. No request data can
    # flip this flag, the demo user is transient (never persisted) and the behaviour is covered by
    # tests/security/test_auth_bypass_edge_cases.py.
    if getattr(settings, "AUTH_DISABLED", False):
        from ..utils.security import _get_or_create_demo_user

        demo_user = await _get_or_create_demo_user(db)
        _bind_interaction_user(request, demo_user)
        return demo_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # With auto_error=False, credentials is None when no/invalid Authorization
    # header was supplied — treat that as an unauthorized request.
    if credentials is None or not credentials.credentials:
        raise credentials_exception

    try:
        payload = verify_access_token(credentials.credentials)
        # Use 'user_id' which is populated by verify_token from either 'sub' or 'user_id'
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    _bind_interaction_user(request, user)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (and gate accounts still awaiting approval)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    if getattr(current_user, "role", "pending") == "pending" and not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is awaiting admin approval.",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency that requires the caller to be an admin.

    When AUTH_DISABLED is on the demo user is an admin, so admin-only routes stay
    reachable in the no-login mode; with auth enforced a non-admin gets 403.
    """
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def _role_at_least(user: User, *roles: str) -> bool:
    if getattr(user, "is_admin", False):
        return True
    return getattr(user, "role", "pending") in roles


async def require_approved(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Allow any user who has been granted a role; block 'pending' accounts.

    A freshly signed-in Google user is 'pending' until an admin grants access —
    they get a clear 403 instead of seeing data.
    """
    if _role_at_least(current_user, "admin", "editor", "viewer"):
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Your account is awaiting admin approval.",
    )


async def require_editor(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require editor or admin — viewers (and pending) cannot modify data."""
    if _role_at_least(current_user, "admin", "editor"):
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Editor or admin privileges are required to make changes.",
    )


# Routes
@router.get("/config")
async def auth_config():
    """Public: lets the frontend discover whether login is currently required.

    Returns ``{"auth_disabled": bool}``. When True the frontend skips the login
    screen and runs as the shared demo user. No authentication is required to
    read this so the SPA can decide its flow before any token exists.
    """
    return {"auth_disabled": bool(getattr(settings, "AUTH_DISABLED", False))}


# NOTE: The public self-service ``POST /register`` endpoint was removed during the
# unused-endpoint audit (see docs/ENDPOINT_AUDIT.md). It was never called by the
# frontend (accounts are created by admins via ``POST /api/users/``) and the
# bootstrap admin is seeded from env by ``seed_admin_user()`` — so the endpoint
# was dead code *and* an unauthenticated user-creation attack surface. Removed
# rather than tagged internal because keeping it live (even hidden from the
# schema) would still expose anonymous account creation.


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return access token.

    Accepts OAuth2 password-flow form-encoded credentials (``username`` and
    ``password``) to stay consistent with the ``OAuth2PasswordBearer`` scheme and
    the frontend, which posts ``application/x-www-form-urlencoded`` to this route.
    A JSON body (``{"username" | "email", "password"}``) is also accepted; both
    encodings are handled identically by ``_extract_login_credentials``.

    Brute-force protection: failed attempts are throttled (HTTP 429) after
    ``LOGIN_RATE_LIMIT_PER_MINUTE`` failures per minute and the account is locked
    (HTTP 423) for ``ACCOUNT_LOCKOUT_MINUTES`` after
    ``ACCOUNT_LOCKOUT_THRESHOLD`` failures.
    """
    username, password = await _extract_login_credentials(request)

    # Basic input-length validation for the (un-modelled) credential fields.
    if not username or len(username) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid username",
        )
    if not password or len(password) > 128:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid password",
        )

    rate_key = _client_key(request, username)

    # Enforce rate limiting / account lockout *before* touching the database.
    rl_status = login_rate_limiter.check(rate_key)
    if rl_status == RateLimitStatus.LOCKED:
        # Security event: surface lockouts so their rate is observable in prod
        # logs/metrics (never log the password or full key).
        logger.warning("auth.login.locked username=%s", username.lower())
        _log_login_attempt_to_redis(rate_key, success=False)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=(
                "Account temporarily locked due to too many failed login "
                "attempts. Please try again later."
            ),
        )
    if rl_status == RateLimitStatus.RATE_LIMITED:
        logger.warning("auth.login.rate_limited username=%s", username.lower())
        _log_login_attempt_to_redis(rate_key, success=False)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please slow down and try again.",
            headers={"Retry-After": "60"},
        )

    # Find user by username OR email — the JSON body explicitly advertises
    # {"username" | "email"} as the identifier, so both must actually match.
    result = await db.execute(
        select(User).where(
            or_(
                User.username == username.lower(),
                func.lower(User.email) == username.lower(),
            )
        )
    )
    user = result.scalars().first()

    if user is None or not verify_password(password, user.hashed_password):
        # Record the failure for brute-force accounting (never log the password).
        login_rate_limiter.register_failure(rate_key)
        _log_login_attempt_to_redis(rate_key, success=False)
        logger.warning("auth.login.failed username=%s", username.lower())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Successful login clears the brute-force counter for this key.
    login_rate_limiter.reset(rate_key)
    _log_login_attempt_to_redis(rate_key, success=True)
    logger.info("auth.login.success user_id=%s", user.id)

    from app.services.audit import record_audit
    await record_audit(
        action="login", entity_type="auth", entity_id=user.id,
        detail=f"User '{user.username}' logged in", user=user, request=request, db=db,
    )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    # Update fields if provided
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name

    if update_data.email is not None:
        # Check if email is already used by another user
        result = await db.execute(
            select(User).where(
                User.email == update_data.email.lower(),
                User.id != current_user.id
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = update_data.email.lower()

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change the current user's password."""
    # In no-login (AUTH_DISABLED) mode the current user is a transient demo user
    # with no real stored password — changing it is not meaningful.
    if getattr(settings, "AUTH_DISABLED", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is unavailable while login is disabled",
        )

    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    await db.commit()

    from app.services.audit import record_audit
    await record_audit(
        action="update", entity_type="auth", entity_id=current_user.id,
        detail="Changed own password", user=current_user, request=request, db=db,
    )

    return {"message": "Password updated successfully"}


@router.post("/logout", response_model=dict)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_active_user),
):
    """Logout user by revoking (blacklisting) the presented access token.

    The token's ``jti`` claim is added to the blacklist until it would have
    naturally expired, so the same token can no longer be used even though its
    signature remains valid.
    """
    if credentials is not None and credentials.credentials:
        try:
            payload = verify_access_token(credentials.credentials)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti:
                token_blacklist.revoke(jti, expires_at=float(exp) if exp else None)
        except HTTPException:
            # Token already invalid/expired — nothing to revoke.
            pass
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    # Update last login
    current_user.last_login = datetime.utcnow()
    await db.commit()

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": current_user.id, "username": current_user.username},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(current_user)
    )


@router.post("/verify", response_model=dict)
async def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    """Verify if token is valid"""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username
    }
