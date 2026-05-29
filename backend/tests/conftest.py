"""Test configuration and fixtures"""
import pytest
import asyncio
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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
        is_admin=False
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
        is_admin=True
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