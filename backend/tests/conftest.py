"""Test configuration and fixtures"""
import pytest
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.utils.security import hash_password
from app.utils.rate_limit import login_rate_limiter
from app.utils.token_blacklist import token_blacklist
from app.config import settings as app_settings


@pytest.fixture(autouse=True)
def _reset_security_state():
    """Clear brute-force/token-revocation state and ENFORCE auth for every test.

    These stores are process-global singletons, so without this isolation a
    rate-limited account or revoked token from one test would leak into the
    next. We also pin AUTH_DISABLED=False so the suite always exercises the real
    authentication path even though the app currently ships with it bypassed.
    """
    previous_auth_disabled = app_settings.AUTH_DISABLED
    app_settings.AUTH_DISABLED = False
    login_rate_limiter.reset_all()
    token_blacklist.reset_all()
    yield
    login_rate_limiter.reset_all()
    token_blacklist.reset_all()
    app_settings.AUTH_DISABLED = previous_auth_disabled


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test async engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=True,
)

# Create test session maker
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
async def _dispose_test_engine():
    """Tear the in-memory engine down at the end of the session.

    The engine uses a ``StaticPool`` so a single aiosqlite connection — backed by
    a dedicated worker thread — is reused for the whole run. If that connection
    is never disposed, the worker thread stays blocked on its queue and the
    interpreter hangs at shutdown waiting to join it (the test results print, but
    the process never exits, so CI kills it and reports the suite as failed).

    Disposing here, while the session event loop is still running, closes the
    connection and lets the worker thread exit cleanly.

    NOTE: the legacy ``event_loop`` fixture that used to live here was removed.
    pytest-asyncio >= 0.23 ignores a user-defined ``event_loop`` fixture and
    drives the loop scope via ``asyncio_default_{fixture,test}_loop_scope`` (set
    to ``session`` in pyproject.toml) instead — which is what keeps this
    session-scoped connection and the tests on one shared loop.
    """
    yield
    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        is_active=True,
        is_admin=False,
        role="editor",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin test user"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        full_name="Admin User",
        is_active=True,
        is_admin=True,
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for test user"""
    login_data = {
        "username": test_user.username,
        "password": "testpass123"
    }
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, admin_user: User) -> dict:
    """Get authentication headers for admin user"""
    login_data = {
        "username": admin_user.username,
        "password": "admin123"
    }
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_customer(db_session: AsyncSession) -> Customer:
    """Create a test customer"""
    customer = Customer(
        account_no="ACC001",
        name="Test Customer",
        account_type=AccountType.RETAIL,
        status=CustomerStatus.ACTIVE,
        email="customer@test.com",
        phone="1234567890",
        branch="Main Branch"
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


@pytest.fixture
async def test_facility(db_session: AsyncSession, test_customer: Customer) -> Facility:
    """Create a test facility"""
    from datetime import date
    facility = Facility(
        customer_id=test_customer.id,
        facility_type=FacilityType.LOAN,
        name="Test Loan",
        status=FacilityStatus.ACTIVE,
        amount=100000.00,
        outstanding=50000.00,
        currency="AED",
        start_date=date.today(),
        expiry_date=date(2024, 12, 31),
        interest_rate=5.5,
        tenor_months="12"
    )
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)
    return facility