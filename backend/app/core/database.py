"""
Database Configuration
پیکربندی دیتابیس
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


def get_database_url() -> str:
    """Convert database URL to async format"""
    url = settings.DATABASE_URL
    if not url:
        return "postgresql+asyncpg://localhost/banking"

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


# Connection pooling for better performance
USE_POOL = os.getenv('USE_CONNECTION_POOL', 'true').lower() == 'true'

if USE_POOL:
    engine = create_async_engine(
        get_database_url(),
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )
else:
    engine = create_async_engine(
        get_database_url(),
        echo=settings.DEBUG,
        pool_pre_ping=True,
        poolclass=NullPool,
    )

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
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
    """Initialize database tables"""
    from app.models.base import Base
    from app.models import user, customer, facility, checklist, settings as settings_model

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
