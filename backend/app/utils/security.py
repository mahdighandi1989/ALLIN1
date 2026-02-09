# backend/app/utils/security.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db

# Conditional import for type hinting to avoid circular dependency.
if TYPE_CHECKING:
    from app.models.user import User

# Password hashing context using bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token-based authentication.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# JWT settings from config.
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class TokenData(BaseModel):
    """Token data validation model"""
    user_id: str
    username: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with unified structure.

    Token structure includes both standard JWT claims and custom claims
    for comprehensive validation and compatibility.
    """
    if not data or not isinstance(data, dict):
        raise ValueError("Token data must be a non-empty dictionary")

    # Validate required fields
    if "user_id" not in data or "username" not in data:
        raise ValueError("Token data must contain user_id and username")

    # Validate data using TokenData model
    try:
        TokenData(user_id=data["user_id"], username=data["username"])
    except Exception as e:
        raise ValueError(f"Invalid token data: {e}")

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Unified token structure with both standard and custom claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        # Standard JWT claims
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "sub": data.get("user_id"),
        "jti": f"{data.get('user_id')}_{int(datetime.now(timezone.utc).timestamp())}"
    })

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create token: {e}")


def verify_access_token(token: str) -> dict:
    """Verify and decode JWT token with unified validation.

    Supports both old token format (user_id, username, type) and new format
    (with additional iss, aud, sub claims) for backward compatibility.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode with issuer and audience validation if present
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require_exp": True,
            }
        )

        # Validate token type (required for all tokens)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Try to get user_id from multiple sources for compatibility
        # New tokens use 'sub', old tokens use 'user_id'
        user_id = payload.get("user_id") or payload.get("sub")
        username = payload.get("username")

        if not user_id or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Ensure user_id is in payload for downstream consumers
        payload["user_id"] = user_id

        # Validate field formats using TokenData model
        try:
            TokenData(user_id=user_id, username=username)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Optional: Validate issuer and audience if present (for new tokens)
        if payload.get("iss") and payload.get("iss") != settings.JWT_ISSUER:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("aud") and payload.get("aud") != settings.JWT_AUDIENCE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> "User":
    """
    Dependency to get the current user from a JWT token.
    Raises HTTPException if the user is not found or the token is invalid.
    """
    # Local import to break the circular dependency.
    from app.models.user import User

    # If authentication is disabled, return a demo user.
    if settings.AUTH_DISABLED:
        result = await db.execute(select(User).where(User.username == "demo"))
        user = result.scalar_one_or_none()
        if user is None:
            # Create a demo user if it doesn't exist.
            user = User(
                username="demo",
                email="demo@example.com",
                hashed_password=hash_password("demo"),
                full_name="Demo User",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = verify_access_token(token)
    user_id: Optional[str] = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


async def get_optional_current_user(
    db: AsyncSession = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)
) -> Optional["User"]:
    """
    Dependency to get the current user if a token is provided.
    Returns None if no token is provided or the token is invalid.
    """
    # Local import to break the circular dependency.
    from app.models.user import User

    # If authentication is disabled, return a demo user.
    if settings.AUTH_DISABLED:
        result = await db.execute(select(User).where(User.username == "demo"))
        user = result.scalar_one_or_none()
        if user is None:
            # Create a demo user if it doesn't exist.
            user = User(
                username="demo",
                email="demo@example.com",
                hashed_password=hash_password("demo"),
                full_name="Demo User",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    if not token:
        return None
    try:
        # Re-use the get_current_user logic
        return await get_current_user(db=db, token=token)
    except HTTPException:
        # If token is invalid, simply return None instead of raising an error
        return None
