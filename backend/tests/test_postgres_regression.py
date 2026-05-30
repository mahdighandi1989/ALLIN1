"""Regression tests that run against a REAL PostgreSQL database.

SQLite (used by the rest of the suite) is forgiving about numeric precision and
schema drift, which is exactly why a production-only class of bug slipped
through: e.g. ``amount * interest_rate`` overflowing ``NUMERIC(5,2)``, or the
live ``users`` table carrying a legacy NOT NULL ``role`` column the models don't
define. These tests reproduce that on Postgres.

They are skipped automatically unless a Postgres URL is available via
``TEST_POSTGRES_URL`` (or a local server on 127.0.0.1:5432), so the normal
SQLite suite is unaffected.
"""
import os
import socket
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


def _pg_url() -> str | None:
    url = os.getenv("TEST_POSTGRES_URL")
    if url:
        return url
    # Fall back to a local server if one is listening.
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=1):
            pass
    except OSError:
        return None
    user = os.getenv("PGUSER", "postgres")
    pw = os.getenv("PGPASSWORD", "postgres")
    return f"postgresql+asyncpg://{user}:{pw}@127.0.0.1:5432/postgres"


PG_URL = _pg_url()
pytestmark = pytest.mark.skipif(
    PG_URL is None, reason="no PostgreSQL available (set TEST_POSTGRES_URL)"
)


@pytest_asyncio.fixture
async def legacy_pg():
    """Create a throwaway DB whose `users` table mirrors the production drift."""
    admin = create_async_engine(PG_URL, isolation_level="AUTOCOMMIT")
    db_name = f"allin1_test_{uuid.uuid4().hex[:12]}"
    async with admin.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin.dispose()

    db_url = PG_URL.rsplit("/", 1)[0] + f"/{db_name}"
    eng = create_async_engine(db_url)
    async with eng.begin() as conn:
        # Legacy users table: has NOT NULL `role`, and is MISSING `is_admin`.
        await conn.execute(
            text(
                """
                CREATE TABLE users (
                    id VARCHAR(8) PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    role VARCHAR(20) NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    last_login TIMESTAMPTZ
                )
                """
            )
        )
        await conn.execute(
            text(
                "INSERT INTO users (id, username, email, hashed_password, role) "
                "VALUES ('old00001','olduser','old@x.ae','x','admin')"
            )
        )
    yield eng, db_url
    await eng.dispose()
    admin = create_async_engine(PG_URL, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :n AND pid <> pg_backend_pid()"
            ).bindparams(n=db_name)
        )
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
    await admin.dispose()


@pytest.mark.asyncio
async def test_bootstrap_and_endpoints_on_legacy_postgres(legacy_pg, monkeypatch):
    """End-to-end: self-heal a drifted Postgres DB, then all endpoints return 200."""
    eng, db_url = legacy_pg

    # Point the app's engine/session at the throwaway DB.
    import app.database as database
    import app.db_init as db_init
    import app.config as config

    monkeypatch.setattr(config.settings, "AUTH_DISABLED", True)
    test_engine = create_async_engine(db_url)
    test_sessionmaker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "AsyncSessionLocal", test_sessionmaker)
    monkeypatch.setattr(db_init, "engine", test_engine)
    monkeypatch.setattr(db_init, "AsyncSessionLocal", test_sessionmaker)

    async def override_db():
        async with test_sessionmaker() as s:
            yield s

    from app.main import app
    from app.database import get_db

    app.dependency_overrides[get_db] = override_db
    try:
        # 1) Self-heal the drifted schema + seed demo data.
        await db_init.init_database()

        # 2) The legacy NOT NULL `role` is relaxed and `is_admin` was added.
        async with test_engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "SELECT column_name, is_nullable FROM information_schema.columns "
                        "WHERE table_name='users'"
                    )
                )
            ).all()
        cols = {r[0]: r[1] for r in rows}
        assert "is_admin" in cols
        assert cols["role"] == "YES"  # NOT NULL relaxed

        # 3) The exact endpoints that 500'd in production now return 200.
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://t") as ac:
            assert (await ac.get("/api/auth/me")).status_code == 200
            assert (await ac.get("/api/customers/")).status_code == 200
            assert (await ac.get("/api/facilities/")).status_code == 200
            dash = await ac.get("/api/stats/dashboard")
        assert dash.status_code == 200
        data = dash.json()
        # Seeded data is present and monthly_revenue did NOT overflow.
        assert data["total_customers"] >= 5
        assert data["monthly_revenue"] > 0
        assert data["total_exposure"]["amount"] > 1_000_000
    finally:
        app.dependency_overrides.pop(get_db, None)
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_monthly_revenue_no_overflow_large_amounts(legacy_pg, monkeypatch):
    """A large amount * rate must not overflow NUMERIC(5,2) on Postgres."""
    eng, db_url = legacy_pg
    import app.database as database
    import app.db_init as db_init

    test_engine = create_async_engine(db_url)
    test_sessionmaker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "AsyncSessionLocal", test_sessionmaker)
    monkeypatch.setattr(db_init, "engine", test_engine)
    monkeypatch.setattr(db_init, "AsyncSessionLocal", test_sessionmaker)
    try:
        await db_init.ensure_schema()
        from decimal import Decimal
        from app.models.customer import Customer
        from app.models.facility import Facility, FacilityType, FacilityStatus
        from sqlalchemy import select, func, and_, cast as sa_cast, Float

        async with test_sessionmaker() as s:
            c = Customer(account_no="BIG-1", name="Mega Corp")
            s.add(c)
            await s.flush()
            s.add(
                Facility(
                    customer_id=c.id, facility_type=FacilityType.LOAN,
                    amount=Decimal("9999999999999.99"), interest_rate=Decimal("99.99"),
                    status=FacilityStatus.ACTIVE, risk_rating="low",
                )
            )
            await s.commit()

        async with test_sessionmaker() as s:
            # This is the previously-overflowing expression.
            val = (
                await s.execute(
                    select(
                        func.coalesce(
                            func.sum(
                                sa_cast(Facility.amount, Float)
                                * sa_cast(func.coalesce(Facility.interest_rate, 0), Float)
                                / 1200.0
                            ),
                            0.0,
                        )
                    ).where(and_(Facility.is_deleted == False, Facility.status == "active"))
                )
            ).scalar()
        assert float(val) > 0
    finally:
        await test_engine.dispose()
