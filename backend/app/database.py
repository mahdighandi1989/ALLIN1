from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import asyncio
from typing import AsyncGenerator
import logging

from app.core.config import settings

# Base class for all SQLAlchemy models
Base = declarative_base()

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection and create connection pool.
    """
    try:
        # Test connection
        async with engine.begin() as conn:
            # Import all models to ensure they are registered with Base
            from app.models import customer, facility, user, audit  # noqa
            
            logger.info("Database connection established successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """
    Close database connection pool.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


async def create_tables() -> None:
    """
    Create all tables if they don't exist.
    """
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they are registered with Base
            from app.models import customer, facility, user, audit  # noqa
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def drop_tables() -> None:
    """
    Drop all tables. Use with caution!
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
            
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


async def health_check() -> bool:
    """
    Check database health.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with async_session_maker() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Context manager for database transactions
class DatabaseTransaction:
    """
    Context manager for database transactions with automatic rollback on error.
    """
    
    def __init__(self):
        self.session: AsyncSession = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = async_session_maker()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"Transaction rolled back due to error: {exc_val}")
        else:
            await self.session.commit()
        
        await self.session.close()


# Utility function for retrying database operations
async def retry_db_operation(operation, max_retries: int = 3, delay: float = 1.0):
    """
    Retry database operation with exponential backoff.
    
    Args:
        operation: Async function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
    """
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                raise
            
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)