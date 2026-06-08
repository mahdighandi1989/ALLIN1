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
                    legacy_dept VARCHAR(20) NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    last_login TIMESTAMPTZ
                )
                """
            )
        )
        await conn.execute(
            text(
                "INSERT INTO users (id, username, email, hashed_password, role, legacy_dept) "
                "VALUES ('old00001','olduser','old@x.ae','x','admin','ops')"
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

        # 2) A legacy unknown NOT NULL column (`legacy_dept`) is relaxed so the
        #    app's INSERTs (which never set it) don't fail; `is_admin` was added;
        #    `role` is now a first-class model column (NOT NULL by design) and is
        #    promoted to 'admin' for the legacy is-admin user by sync_user_roles.
        async with test_engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "SELECT column_name, is_nullable FROM information_schema.columns "
                        "WHERE table_name='users'"
                    )
                )
            ).all()
            legacy_role = (
                await conn.execute(text("SELECT role, is_admin FROM users WHERE id='old00001'"))
            ).one()
        cols = {r[0]: r[1] for r in rows}
        assert "is_admin" in cols and "role" in cols
        assert cols["legacy_dept"] == "YES"  # unknown legacy NOT NULL relaxed
        assert legacy_role[0] == "admin" and legacy_role[1] is True  # role/is_admin synced

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
async def test_legacy_uppercase_enums_and_blank_email(legacy_pg, monkeypatch):
    """Legacy UPPERCASE enum labels + blank emails must not 500 list endpoints.

    Reproduces three production-only bugs invisible to SQLite:
      * enums persisted as NAME ('CORPORATE') vs the model value ('corporate'),
      * an empty-string email that a strict EmailStr response would reject,
      * (implicitly) the enum/value mismatch on == filters.
    """
    eng, db_url = legacy_pg
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

    # Seed a legacy customers table with UPPERCASE enum labels + a blank email,
    # mirroring a real old database.
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE TYPE accounttype AS ENUM ('RETAIL','CORPORATE','SME')"))
        await conn.execute(text("CREATE TYPE customerstatus AS ENUM ('ACTIVE','INACTIVE','SUSPENDED')"))
        await conn.execute(
            text(
                "CREATE TABLE customers (id VARCHAR(33) PRIMARY KEY, account_no VARCHAR(50) UNIQUE NOT NULL,"
                " name VARCHAR(200) NOT NULL, account_type accounttype, status customerstatus,"
                " email VARCHAR(100), is_deleted BOOLEAN DEFAULT false, created_at TIMESTAMPTZ DEFAULT now())"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO customers (id, account_no, name, account_type, status, email) VALUES"
                " ('c1','OLD-1','Legacy Corp','CORPORATE','ACTIVE',''),"
                " ('c2','OLD-2','Legacy Retail','RETAIL','ACTIVE','x@y.ae')"
            )
        )

    async def override_db():
        async with test_sessionmaker() as s:
            yield s

    from app.main import app
    from app.database import get_db

    app.dependency_overrides[get_db] = override_db
    try:
        await db_init.init_database()
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://t") as ac:
            r = await ac.get("/api/customers/")
            assert r.status_code == 200, r.text
            assert r.json()["total"] >= 2
            # The == enum filter works against the lowercased label.
            rf = await ac.get("/api/customers/?account_type=corporate")
            assert rf.status_code == 200
            assert rf.json()["total"] >= 1
            assert (await ac.get("/api/customers/stats/summary")).status_code == 200
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


@pytest.mark.asyncio
async def test_uppercase_varchar_enums_are_canonicalised(legacy_pg, monkeypatch):
    """VARCHAR enum columns holding UPPERCASE values must be lowercased in place.

    Distinct from the native-enum test above: here the columns are plain VARCHAR
    (the state prod reaches after schema-sync converts a native enum to varchar,
    OR when the column was native_enum=False from the start). Values like
    'CORPORATE'/'LOAN' are valid once lowercased, so the old coerce-to-default
    step skipped them and they stayed UPPERCASE — TolerantEnum then coerced
    'CORPORATE'->retail and 'LOAN'->other on every read (the exact production
    log symptom and the "Customers by Type" / facility-type dashboard bug).
    normalize_enum_data() must rewrite them to the canonical lowercase value,
    while still mapping legacy aliases (OD->overdraft) and coercing true garbage.
    """
    eng, db_url = legacy_pg
    import app.db_init as db_init

    test_engine = create_async_engine(db_url)
    test_sessionmaker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_init, "engine", test_engine)
    monkeypatch.setattr(db_init, "AsyncSessionLocal", test_sessionmaker)

    # Pre-create the tables as VARCHAR(50) so legacy values of any length fit,
    # mirroring prod after the native-enum -> varchar conversion.
    async with test_engine.begin() as conn:
        await conn.execute(
            text(
                "CREATE TABLE customers (id VARCHAR(36) PRIMARY KEY,"
                " account_no VARCHAR(50) UNIQUE NOT NULL, name VARCHAR(200) NOT NULL,"
                " account_type VARCHAR(50), status VARCHAR(50),"
                " is_deleted BOOLEAN DEFAULT false, created_at TIMESTAMPTZ DEFAULT now())"
            )
        )
        await conn.execute(
            text(
                "CREATE TABLE facilities (id VARCHAR(33) PRIMARY KEY,"
                " customer_id VARCHAR(36) NOT NULL, name VARCHAR(200),"
                " facility_type VARCHAR(50), status VARCHAR(50),"
                " amount NUMERIC(18,2) DEFAULT 0, outstanding NUMERIC(18,2) DEFAULT 0,"
                " currency VARCHAR(3) DEFAULT 'AED',"
                " is_deleted BOOLEAN DEFAULT false, created_at TIMESTAMPTZ DEFAULT now())"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO customers (id, account_no, name, account_type, status) VALUES"
                " ('u1','UC-1','Up Corp','CORPORATE','ACTIVE'),"      # valid-but-UPPERCASE
                " ('u2','UC-2','Up Retail','RETAIL','active'),"
                " ('u3','UC-3','Legacy Indiv','INDIVIDUAL','INACTIVE'),"  # alias
                " ('u4','UC-4','Garbage','ZZZ','???')"                 # true garbage -> default
            )
        )
        await conn.execute(
            text(
                "INSERT INTO facilities (id, customer_id, name, facility_type, status) VALUES"
                " ('f1','u1','Loan A','LOAN','ACTIVE'),"               # valid-but-UPPERCASE
                " ('f2','u1','OD B','OD','active'),"                   # alias
                " ('f3','u2','LC C','LC','CLOSED'),"
                " ('f4','u3','Mystery','WTF','???')"                   # true garbage -> default
            )
        )

    try:
        # ensure_schema() adds any missing model columns; normalize_enum_data()
        # canonicalises the dirty values. (Both are what init_database runs.)
        await db_init.ensure_schema()
        await db_init.normalize_enum_data()

        # 1) Stored values are now canonical lowercase / mapped / coerced.
        async with test_engine.connect() as conn:
            cust = dict(
                (r[0], r[1]) for r in (
                    await conn.execute(text("SELECT account_no, account_type FROM customers"))
                ).all()
            )
            cstat = dict(
                (r[0], r[1]) for r in (
                    await conn.execute(text("SELECT account_no, status FROM customers"))
                ).all()
            )
            fac = dict(
                (r[0], r[1]) for r in (
                    await conn.execute(text("SELECT name, facility_type FROM facilities"))
                ).all()
            )
        assert cust == {"UC-1": "corporate", "UC-2": "retail",
                        "UC-3": "retail", "UC-4": "retail"}, cust   # UPPERCASE fixed, alias+garbage too
        assert cstat["UC-1"] == "active" and cstat["UC-3"] == "inactive", cstat
        assert fac == {"Loan A": "loan", "OD B": "overdraft",
                       "LC C": "lc", "Mystery": "other"}, fac       # LOAN no longer -> other

        # 2) Reading through the ORM/TolerantEnum yields zero coercion (the prod log).
        import warnings
        from sqlalchemy import select as sa_select
        from app.models.customer import Customer
        from app.models.facility import Facility
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            async with test_sessionmaker() as s:
                custs = (await s.execute(sa_select(Customer))).scalars().all()
                facs = (await s.execute(sa_select(Facility))).scalars().all()
            coerced = [str(w.message) for w in caught if "coerc" in str(w.message).lower()]
        assert coerced == [], coerced
        assert {c.account_no: c.account_type.value for c in custs}["UC-1"] == "corporate"
        assert {f.name: f.facility_type.value for f in facs}["Loan A"] == "loan"
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_narrow_varchar_column_is_widened_to_model(legacy_pg, monkeypatch):
    """An existing varchar narrower than the model must be widened by schema-sync.

    Reproduces the production bug where facilities.customer_id was first created
    varchar(33) and later widened to varchar(36) in the model (real customer ids
    are 36-char UUIDs). create_all / ADD COLUMN never ALTER an existing column,
    so the live column stayed varchar(33); every facility INSERT with a 36-char
    customer_id then failed with "value too long for type character varying(33)",
    rolling back the entire data-merge step and leaving facilities with no amounts
    (Monthly Revenue / AED exposure stuck at 0 on the dashboard).
    """
    eng, db_url = legacy_pg
    import app.db_init as db_init

    test_engine = create_async_engine(db_url)
    monkeypatch.setattr(db_init, "engine", test_engine)

    async with test_engine.begin() as conn:
        await conn.execute(
            text(
                "CREATE TABLE customers (id VARCHAR(36) PRIMARY KEY,"
                " account_no VARCHAR(50) UNIQUE NOT NULL, name VARCHAR(200) NOT NULL,"
                " is_deleted BOOLEAN DEFAULT false, created_at TIMESTAMPTZ DEFAULT now())"
            )
        )
        # facilities.customer_id deliberately too narrow (the legacy width).
        await conn.execute(
            text(
                "CREATE TABLE facilities (id VARCHAR(33) PRIMARY KEY,"
                " customer_id VARCHAR(33) NOT NULL, name VARCHAR(200),"
                " amount NUMERIC(18,2) DEFAULT 0, currency VARCHAR(3) DEFAULT 'AED',"
                " is_deleted BOOLEAN DEFAULT false, created_at TIMESTAMPTZ DEFAULT now())"
            )
        )

    try:
        # Before: a 36-char customer_id does NOT fit.
        async with test_engine.connect() as conn:
            before = (
                await conn.execute(
                    text(
                        "SELECT character_maximum_length FROM information_schema.columns "
                        "WHERE table_name='facilities' AND column_name='customer_id'"
                    )
                )
            ).scalar()
        assert before == 33

        await db_init.ensure_schema()  # must widen customer_id 33 -> 36 (model width)

        async with test_engine.connect() as conn:
            after = (
                await conn.execute(
                    text(
                        "SELECT character_maximum_length FROM information_schema.columns "
                        "WHERE table_name='facilities' AND column_name='customer_id'"
                    )
                )
            ).scalar()
        assert after >= 36, after

        # And a 36-char-UUID-keyed facility now inserts without truncation.
        async with test_engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO customers (id, account_no, name) "
                    "VALUES ('dbcbfebf-5ae1-428e-8ba6-a0de5b8d10c1','W-1','Wide Co')"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO facilities (id, customer_id, name, amount) "
                    "VALUES ('F-1','dbcbfebf-5ae1-428e-8ba6-a0de5b8d10c1','Loan',1000)"
                )
            )
            linked = (
                await conn.execute(text("SELECT customer_id FROM facilities WHERE id='F-1'"))
            ).scalar()
        assert linked == "dbcbfebf-5ae1-428e-8ba6-a0de5b8d10c1"
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_type_drift_and_orphan_pk_are_reconciled(legacy_pg, monkeypatch):
    """Legacy columns with the wrong TYPE / an orphan NOT-NULL PK must be repaired.

    The production /run-merge report showed every failing step was the same class
    of bug — a column created by an older model with a different type than the
    model now declares, which create_all never alters:
      * facilities.tenor_months  integer       (model String) }  asyncpg: "column
      * attachments.file_size     bigint        (model String) }  X is of type ..
      * custom_tasks.completed_date timestamptz (model String) }  but expression
                                                                  is character varying"
      * customer_profiles.id      orphan NOT-NULL PRIMARY KEY the model never sets
                                  → "null value in column id violates not-null".
    schema-sync must stringify the type-drifted columns and give the orphan PK a
    generating default, so the merge INSERTs (which send strings / omit id) work.
    """
    eng, db_url = legacy_pg
    import app.db_init as db_init

    test_engine = create_async_engine(db_url)
    monkeypatch.setattr(db_init, "engine", test_engine)

    # Start from the real model schema, then introduce the exact production drift.
    await db_init.ensure_schema()
    async with test_engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text("ALTER TABLE facilities ALTER COLUMN tenor_months TYPE integer USING NULL"))
        await conn.execute(text("ALTER TABLE attachments ALTER COLUMN file_size TYPE bigint USING NULL"))
        await conn.execute(text("ALTER TABLE custom_tasks ALTER COLUMN completed_date TYPE timestamptz USING NULL"))
        # customer_profiles: legacy orphan `id` PK (model's PK is account_no, no id).
        await conn.execute(text("ALTER TABLE customer_profiles DROP CONSTRAINT customer_profiles_pkey"))
        await conn.execute(text("ALTER TABLE customer_profiles ADD COLUMN id varchar(60)"))
        await conn.execute(text("ALTER TABLE customer_profiles ALTER COLUMN id SET NOT NULL"))
        await conn.execute(text("ALTER TABLE customer_profiles ADD PRIMARY KEY (id)"))

    try:
        await db_init.ensure_schema()  # must stringify the drift + default the orphan PK

        async def coltype(table, col):
            async with test_engine.connect() as conn:
                return (
                    await conn.execute(
                        text(
                            "SELECT data_type FROM information_schema.columns "
                            "WHERE table_name=:t AND column_name=:c"
                        ).bindparams(t=table, c=col)
                    )
                ).scalar()

        # 1) Type-drifted columns are now character types (no more datatype mismatch).
        assert (await coltype("facilities", "tenor_months")) in ("text", "character varying")
        assert (await coltype("attachments", "file_size")) in ("text", "character varying")
        assert (await coltype("custom_tasks", "completed_date")) in ("text", "character varying")

        # 2) The orphan id PK now has a generating default, so an INSERT that omits
        #    it (exactly what the merge does — it only sets account_no etc.) works.
        async with test_engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(
                text("INSERT INTO customer_profiles (account_no, customer_name) VALUES ('505559','Drift Co')")
            )
            await conn.execute(
                text("INSERT INTO customer_profiles (account_no, customer_name) VALUES ('114748','Other Co')")
            )
            rows = (await conn.execute(text("SELECT id, account_no FROM customer_profiles ORDER BY account_no"))).all()
        # Both rows got a non-null, unique, auto-generated id.
        ids = [r[0] for r in rows]
        assert all(i for i in ids) and len(set(ids)) == 2, rows
        assert {r[1] for r in rows} == {"114748", "505559"}

        # 3) And a string tenor_months now inserts into the (formerly integer) column.
        async with test_engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(
                text("INSERT INTO customers (id, account_no, name) VALUES ('c-1','D-1','Cust')")
            )
            await conn.execute(
                text(
                    "INSERT INTO facilities (id, customer_id, name, amount, tenor_months, risk_rating) "
                    "VALUES ('F-1','c-1','Loan',1000,'24','low')"
                )
            )
            tm = (await conn.execute(text("SELECT tenor_months FROM facilities WHERE id='F-1'"))).scalar()
        assert tm == "24"
    finally:
        await test_engine.dispose()
