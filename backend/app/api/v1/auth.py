"""
Authentication API Routes
روت‌های احراز هویت
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    verify_token, get_current_user, TokenData
)
from app.core.config import settings

router = APIRouter()


# ========== Schemas ==========
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# ========== Mock Database (برای تست - در production از دیتابیس واقعی استفاده شود) ==========
# این فقط برای نمایش است - در عمل از SQLAlchemy استفاده می‌شود
mock_users = {
    "admin": {
        "id": "user-001",
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin123"),
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "is_active": True,
        "permissions": ["*"]
    }
}


# ========== Routes ==========
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    ورود به سیستم

    Returns:
        Token با access_token و refresh_token
    """
    # بررسی کاربر
    user = mock_users.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # بررسی رمز عبور
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # بررسی فعال بودن
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # ایجاد توکن‌ها
    token_data = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "permissions": user["permissions"]
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """
    ثبت‌نام کاربر جدید
    """
    # بررسی تکراری نبودن
    if user_data.username in mock_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # بررسی ایمیل
    for u in mock_users.values():
        if u["email"] == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # ایجاد کاربر
    new_user = {
        "id": f"user-{len(mock_users) + 1:03d}",
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "role": "viewer",  # نقش پیش‌فرض
        "is_active": True,
        "permissions": ["read:all"]
    }

    mock_users[user_data.username] = new_user

    return UserResponse(**new_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """
    تازه‌سازی توکن دسترسی
    """
    payload = verify_token(token_data.refresh_token, "refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # ایجاد توکن‌های جدید
    new_token_data = {
        "sub": payload["sub"],
        "username": payload.get("username"),
        "role": payload.get("role"),
        "permissions": payload.get("permissions", [])
    }

    access_token = create_access_token(new_token_data)
    refresh_token = create_refresh_token(new_token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    دریافت اطلاعات کاربر فعلی
    """
    # در عمل از دیتابیس بخوانید
    for user in mock_users.values():
        if user["id"] == current_user.user_id:
            return UserResponse(**user)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """
    خروج از سیستم
    """
    # در عمل، توکن را به blacklist اضافه کنید
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: TokenData = Depends(get_current_user)
):
    """
    تغییر رمز عبور
    """
    # پیدا کردن کاربر
    user = None
    for u in mock_users.values():
        if u["id"] == current_user.user_id:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # بررسی رمز فعلی
    if not verify_password(password_data.current_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # تغییر رمز
    user["hashed_password"] = get_password_hash(password_data.new_password)

    return {"message": "Password changed successfully"}
