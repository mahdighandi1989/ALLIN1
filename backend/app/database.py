from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from urllib.parse import urlsplit
import os
import ssl as ssl_module

from app.config import settings

# Hostnames that are always treated as local (no SSL). An empty host covers a
# unix-socket DSN. We parse the *host* rather than substring-matching the whole
# URL — the old ``'localhost' not in url`` check mis-classified hosts like
# ``localhost.example.com`` (a remote host) as local.
_LOCAL_HOSTS = {None, "", "localhost", "127.0.0.1", "::1"}


def _db_host(database_url: str):
    try:
        return urlsplit(database_url).hostname
    except Exception:
        return None


def _should_use_ssl(database_url: str) -> bool:
    """True for managed remote Postgres (Render etc.); False for sqlite/local."""
    if database_url.startswith("sqlite"):
        return False
    return _db_host(database_url) not in _LOCAL_HOSTS


def _build_connect_args(database_url: str) -> dict:
    """SSL connect args for the async engine.

    Render's managed Postgres terminates TLS with a certificate that does not
    chain to a public CA on the internal network, so by default we connect over
    TLS but do not verify the certificate/hostname (this is the long-standing,
    working production setting). Set ``DB_SSL_VERIFY=true`` to require full
    verification — e.g. behind a CA-signed endpoint — without a code change.
    """
    if not _should_use_ssl(database_url):
        return {}
    ssl_context = ssl_module.create_default_context()
    if os.getenv("DB_SSL_VERIFY", "false").strip().lower() not in ("1", "true", "yes", "on"):
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl_module.CERT_NONE
    return {"ssl": ssl_context}


# SSL configuration for remote databases (Render.com, etc.)
connect_args = _build_connect_args(settings.DATABASE_URL)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    connect_args=connect_args,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create Base class for models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """
    Initialize database (create tables).
    """
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def close_db() -> None:
    """
    Close database connections.
    """
    await engine.dispose()