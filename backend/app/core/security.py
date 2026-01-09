"""
Security Module
ماژول امنیت و احراز هویت
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """تایید رمز عبور"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """هش کردن رمز عبور"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """ایجاد توکن دسترسی"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """ایجاد توکن بازیابی"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """رمزگشایی توکن"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """تایید اعتبار توکن"""
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    exp = payload.get("exp")
    if exp is None:
        return None

    if datetime.utcnow() > datetime.fromtimestamp(exp):
        return None

    return payload


class TokenData:
    """داده‌های توکن"""

    def __init__(
        self,
        user_id: str,
        username: str,
        role: str,
        permissions: list = None
    ):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.permissions = permissions or []


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """دریافت کاربر فعلی از توکن"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token, "access")
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    return TokenData(
        user_id=user_id,
        username=payload.get("username", ""),
        role=payload.get("role", "viewer"),
        permissions=payload.get("permissions", [])
    )


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)):
    """دریافت کاربر فعال"""
    # در اینجا می‌توان بررسی‌های بیشتری انجام داد
    # مثل بررسی فعال بودن کاربر در دیتابیس
    return current_user


def require_permission(permission: str):
    """دکوراتور برای بررسی دسترسی"""

    async def permission_checker(current_user: TokenData = Depends(get_current_active_user)):
        if current_user.role == "admin":
            return current_user

        if "*" in current_user.permissions:
            return current_user

        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission}"
            )
        return current_user

    return permission_checker


def require_role(allowed_roles: list):
    """دکوراتور برای بررسی نقش"""

    async def role_checker(current_user: TokenData = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role not allowed. Required: {allowed_roles}"
            )
        return current_user

    return role_checker


# Rate Limiting
from collections import defaultdict
import time


class RateLimiter:
    """محدودکننده نرخ درخواست"""

    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(
        self,
        key: str,
        max_requests: int = settings.RATE_LIMIT_PER_MINUTE,
        window_seconds: int = 60
    ) -> bool:
        """بررسی مجاز بودن درخواست"""
        now = time.time()
        window_start = now - window_seconds

        # پاکسازی درخواست‌های قدیمی
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

        if len(self.requests[key]) >= max_requests:
            return False

        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()
