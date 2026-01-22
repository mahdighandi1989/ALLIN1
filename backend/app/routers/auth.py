"""Authentication Router"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.utils.security import hash_password, verify_password, create_token, get_current_user, TokenData

router = APIRouter(prefix="/api/auth", tags=["Auth"])


async def ensure_admin(db: AsyncSession):
    """Create default admin if no users exist"""
    result = await db.execute(select(User).limit(1))
    if not result.scalars().first():
        admin = User(
            username="admin",
            email="admin@system.local",
            hashed_password=hash_password("admin123"),
            full_name="Administrator",
            is_admin=True
        )
        db.add(admin)
        await db.commit()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login and get access token"""
    await ensure_admin(db)

    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login = datetime.utcnow()
    await db.commit()

    token = create_token({"sub": user.id, "username": user.username})
    return Token(access_token=token)


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    # Check username
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: TokenData = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user"""
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
