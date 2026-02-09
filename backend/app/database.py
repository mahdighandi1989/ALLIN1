"""Database configuration and session management"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Please set it to your PostgreSQL connection string. "
        "Example: postgresql+asyncpg://username:password@host:port/database"
    )

def _apply_ssl_for_render(url: str) -> str:
    """
    Applies sslmode=require for database URLs hosted on Render.com
    if sslmode is not already specified.
    """
    if "onrender.com" in url and "sslmode" not in url:
        # Check if the URL already has query parameters
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}sslmode=require"
    return url

# Convert DATABASE_URL to async-compatible format
# Render and other cloud providers use various formats:
# - postgres:// (legacy format)
# - postgresql:// (defaults to psycopg2)
# - postgresql+psycopg2:// (explicit psycopg2)
# We need postgresql+asyncpg:// for async SQLAlchemy
def get_async_database_url(url: str) -> str:
    """Convert database URL to use asyncpg driver for async SQLAlchemy"""
    async_url = url
    # Already using asyncpg - no conversion needed
    if "postgresql+asyncpg://" in async_url:
        pass
    # Handle postgresql+psycopg2:// (explicit sync driver)
    elif async_url.startswith("postgresql+psycopg2://"):
        async_url = async_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    # Handle postgresql+psycopg:// (another sync driver variant)
    elif async_url.startswith("postgresql+psycopg://"):
        async_url = async_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    # Handle postgres:// (legacy/shorthand format)
    elif async_url.startswith("postgres://"):
        async_url = async_url.replace("postgres://", "postgresql+asyncpg://", 1)
    # Handle postgresql:// (defaults to psycopg2)
    elif async_url.startswith("postgresql://"):
        async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return _apply_ssl_for_render(async_url)

def get_sync_database_url(url: str) -> str:
    """Convert database URL to use sync driver (psycopg2) for migrations"""
    sync_url = url
    # Handle postgres:// (legacy format) - convert to standard postgresql://
    if sync_url.startswith("postgres://"):
        sync_url = sync_url.replace("postgres://", "postgresql://", 1)

    # Handle asyncpg driver - convert to sync
    if "+asyncpg" in sync_url:
        sync_url = sync_url.replace("+asyncpg", "")

    # Handle explicit psycopg2 - already sync, just normalize
    if "+psycopg2" in sync_url:
        sync_url = sync_url.replace("+psycopg2", "")

    # Handle explicit psycopg - already sync, just normalize
    if "+psycopg" in sync_url:
        sync_url = sync_url.replace("+psycopg", "")

    return _apply_ssl_for_render(sync_url)

ASYNC_DATABASE_URL = get_async_database_url(DATABASE_URL)
SYNC_DATABASE_URL = get_sync_database_url(DATABASE_URL)

# Log the URL conversion (hide sensitive parts)
def _mask_url(url: str) -> str:
    """Mask password in database URL for logging"""
    import re
    return re.sub(r'://[^:]+:[^@]+@', '://***:***@', url)

logger.info(f"Original DATABASE_URL format: {_mask_url(DATABASE_URL)}")
logger.info(f"Async DATABASE_URL format: {_mask_url(ASYNC_DATABASE_URL)}")
logger.info(f"Sync DATABASE_URL format: {_mask_url(SYNC_DATABASE_URL)}")

# Create async engine with connection pool
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=bool(os.getenv("DATABASE_ECHO", "false").lower() == "true"),
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "30")),
    pool_pre_ping=True,
    pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create sync engine for migrations
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=bool(os.getenv("DATABASE_ECHO", "false").lower() == "true"),
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "30")),
    pool_pre_ping=True,
    pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
)

# Create sync session maker for migrations
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()


# Dependency for getting async database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency for FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# Function to create all tables (for development)
async def create_tables():
    """Create all database tables"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


# Function to drop all tables (for development)
async def drop_tables():
    """Drop all database tables"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


# Initialize database
async def init_db():
    """Initialize database connection and create tables if needed"""
    try:
        # Test connection
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Import models to ensure they're registered with Base metadata
        from app.models import User, Customer, Facility
        
        # Create tables if they don't exist
        await create_tables()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


# Close database connections
async def close_db():
    """Close database connections"""
    try:
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Health check function
async def check_database_health() -> bool:
    """Check database connection health"""
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.debug("Database health check passed")
                return True
            else:
                logger.warning("Database health check failed - unexpected result")
                return False
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Database utilities
async def execute_raw_query(query: str, params: dict = None) -> list:
    """Execute raw SQL query and return results"""
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text(query), params or {})
            return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Raw query execution failed: {e}")
        raise


async def get_table_info(table_name: str) -> dict:
    """Get information about a specific table"""
    try:
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = :table_name
        ORDER BY ordinal_position
        """
        columns = await execute_raw_query(query, {"tabl