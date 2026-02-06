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

from app.config import settings, get_settings
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
                detail="Invalid token payload format",
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user with comprehensive validation"""
    from app.models.user import User
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify and decode token
        payload = verify_access_token(credentials.credentials)
        
        # Extract and validate user data from payload
        user_id = payload.get("user_id")
        username = payload.get("username")
        
        # Additional validation (already done in verify_access_token, but double-check)
        if not user_id or not username:
            raise credentials_exception
        
        # Validate user_id format (8 characters, alphanumeric)
        if not isinstance(user_id, str) or len(user_id) != 8 or not re.match(r'^[a-zA-Z0-9]{8}$', user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate username format
        if not isinstance(username, str) or not re.match(r'^[a-zA-Z0-9_-]{3,50}$', username):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Query database with validated parameters
        try:
            result = await db.execute(
                select(User).where(
                    User.id == user_id,
                    User.username == username.lower(),
                    User.is_active == True
                )
            )
            user = result.scalar_one_or_none()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database query failed"
            )
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Final validation - ensure user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise credentials_exception


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
    return current_user


class FakeUser:
    """Fake user for development when AUTH_DISABLED is True"""
    def __init__(self):
        self.id = "dev12345"
        self.username = "developer"
        self.email = "dev@example.com"
        self.full_name = "Developer Mode"
        self.is_active = True
        self.is_admin = True


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user, but return fake user if AUTH_DISABLED is True.
    This allows bypassing authentication for development.
    """
    current_settings = get_settings()

    # If auth is disabled, return fake user
    if current_settings.AUTH_DISABLED:
        return FakeUser()

    # Otherwise, require authentication
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_current_user(credentials, db)


def get_token_data(current_user = Depends(get_current_user)) -> TokenData:
    """Get validated token data from current user"""
    try:
        return TokenData(
            user_id=current_user.id,
            username=current_user.username
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract token data"
        )


def validate_uuid_format(value: str) -> bool:
    """Validate if string is a valid UUID format"""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_input(value: str, max_length: int = 255) -> str:
    """Sanitize string input to prevent injection attacks"""
    if not isinstance(value, str):
        raise ValueError("Input must be a string")
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # Trim whitespace and limit length
    sanitized = sanitized.strip()[:max_length]
    
    return sanitized


def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements"""
    if not password or not isinstance(password, str):
        return False
    
    if len(password) < 8:
        return False
    
    # Must contain at least one digit
    if not any(char.isdigit() for char in password):
        return False
    
    # Must contain at least one letter
    if not any(char.isalpha() for char in password):
        return False
    
    # Must not contain common weak patterns
    weak_patterns = ['123456', 'password', 'qwerty', 'abc123']
    password_lower = password.lower()
    for pattern in weak_patterns:
        if pattern in password_lower:
            return False
    
    return True