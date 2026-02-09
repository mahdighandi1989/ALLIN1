"""Security utilities for password hashing and JWT token management"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, validator
import re
import uuid

from app.core.config import settings
from app.database import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 security scheme
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data model"""
    user_id: str
    username: str
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('user_id is required and must be a string')
        if len(v) != 8:
            raise ValueError('user_id must be exactly 8 characters')
        if not re.match(r'^[a-zA-Z0-9]{8}$', v):
            raise ValueError('user_id contains invalid characters')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('username is required and must be a string')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('username must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('username contains invalid characters')
        return v.lower()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    if not plain or not hashed:
        return False
    if not isinstance(plain, str) or not isinstance(hashed, str):
        return False
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create token: {e}")


def verify_access_token(token: str) -> dict:
    """Verify and decode JWT token with proper validation"""
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate required fields exist
        user_id = payload.get("user_id")
        username = payload.get("username")
        
        if not user_id or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate field formats using TokenData model
        try:
            TokenData(user_id=user_id, username=username)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token data format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user from token"""
    token = credentials.credentials
    payload = verify_access_token(token)
    
    # Fetch user from database
    query = select(User).where(User.id == payload["user_id"], User.username == payload["username"])
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user