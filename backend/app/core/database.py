"""
Database Configuration and Session Management
تنظیمات دیتابیس و مدیریت سشن
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Create async engine
# Use NullPool for serverless environments like Render
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    poolclass=NullPool,  # Better for serverless
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    برای استفاده به عنوان dependency در FastAPI
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create tables
    ایجاد جداول در دیتابیس
    """
    from app.models.base import Base
    # Import all models to register them
    from app.models import (
        user, customer, facility, guarantor, property,
        deposit, kyc, checklist, attachment, note, journal, settings
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
