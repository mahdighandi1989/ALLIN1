from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Database URL configuration - secure defaults without hardcoded credentials
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://localhost/allin1_db"
)

# Validate that DATABASE_URL is properly configured
if not DATABASE_URL or DATABASE_URL == "postgresql+asyncpg://localhost/allin1_db":
    logger.warning(
        "DATABASE_URL not configured or using default. "
        "Please set DATABASE_URL environment variable with proper credentials."
    )

# Create async engine with connection pool
async_engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",  # Only enable in development
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
    pool_pre_ping=True,
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
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
    DATABASE_URL.replace("+asyncpg", ""),
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
    pool_pre_ping=True,
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
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
        
        # Import models to ensure they're registered
        from app.models import User, Customer, Facility
        
        # Create tables
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