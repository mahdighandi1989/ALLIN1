import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

# Schemas
class UserRegister(BaseModel):
    # Explicit length limits + format patterns on every text field guard against
    # oversized payloads and injection-style input (validated by Pydantic, so
    # invalid input is rejected with HTTP 422 before any handler logic runs).
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, hyphens and underscores')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

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


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user using unified token verification."""
    # TEMPORARY: when AUTH_DISABLED is on, bypass auth and use a shared demo user
    # (login removed for now). Set AUTH_DISABLED=false to restore enforcement.
    if getattr(settings, "AUTH_DISABLED", False):
        from ..utils.security import _get_or_create_demo_user

        return await _get_or_create_demo_user(db)

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

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# Routes
@router.get("/config")
async def auth_config():
    """Public: lets the frontend discover whether login is currently required.

    Returns ``{"auth_disabled": bool}``. When True the frontend skips the login
    screen and runs as the shared demo user. No authentication is required to
    read this so the SPA can decide its flow before any token exists.
    """
    return {"auth_disabled": bool(getattr(settings, "AUTH_DISABLED", False))}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username.lower()))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email.lower()))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    user = User(
        username=user_data.username.lower(),
        email=user_data.email.lower(),
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_admin=False
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

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


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return access token.

    Accepts OAuth2 password-flow form-encoded credentials (``username`` and
    ``password``) to stay consistent with the ``OAuth2PasswordBearer`` scheme and
    the frontend, which posts ``application/x-www-form-urlencoded`` to this route.

    Brute-force protection: failed attempts are throttled (HTTP 429) after
    ``LOGIN_RATE_LIMIT_PER_MINUTE`` failures per minute and the account is locked
    (HTTP 423) for ``ACCOUNT_LOCKOUT_MINUTES`` after
    ``ACCOUNT_LOCKOUT_THRESHOLD`` failures.
    """
    # Basic input-length validation for the (un-modelled) OAuth2 form fields.
    if not form_data.username or len(form_data.username) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid username",
        )
    if not form_data.password or len(form_data.password) > 128:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid password",
        )

    rate_key = _client_key(request, form_data.username)

    # Enforce rate limiting / account lockout *before* touching the database.
    rl_status = login_rate_limiter.check(rate_key)
    if rl_status == RateLimitStatus.LOCKED:
        # Security event: surface lockouts so their rate is observable in prod
        # logs/metrics (never log the password or full key).
        logger.warning("auth.login.locked username=%s", form_data.username.lower())
        _log_login_attempt_to_redis(rate_key, success=False)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=(
                "Account temporarily locked due to too many failed login "
                "attempts. Please try again later."
            ),
        )
    if rl_status == RateLimitStatus.RATE_LIMITED:
        logger.warning("auth.login.rate_limited username=%s", form_data.username.lower())
        _log_login_attempt_to_redis(rate_key, success=False)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please slow down and try again.",
            headers={"Retry-After": "60"},
        )

    # Find user by username
    result = await db.execute(select(User).where(User.username == form_data.username.lower()))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        # Record the failure for brute-force accounting (never log the password).
        login_rate_limiter.register_failure(rate_key)
        _log_login_attempt_to_redis(rate_key, success=False)
        logger.warning("auth.login.failed username=%s", form_data.username.lower())
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    await db.commit()

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
