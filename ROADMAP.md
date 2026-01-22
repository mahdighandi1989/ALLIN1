# Banking Operations System - Rebuild Roadmap

> **Goal**: Build a simple, reliable, and maintainable banking operations system from scratch.
> **Philosophy**: Simplicity over features. Get it working first, optimize later.

---

## Table of Contents

1. [Problems to Avoid](#problems-to-avoid)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Phase 1: Backend Foundation](#phase-1-backend-foundation)
5. [Phase 2: Core API Endpoints](#phase-2-core-api-endpoints)
6. [Phase 3: Frontend Implementation](#phase-3-frontend-implementation)
7. [Phase 4: Deployment Configuration](#phase-4-deployment-configuration)
8. [Phase 5: Optional Features](#phase-5-optional-features)
9. [Testing Strategy](#testing-strategy)
10. [Checklist](#checklist)

---

## Problems to Avoid

Learn from past mistakes. These are the issues we **must not repeat**:

| Problem | Root Cause | Solution |
|---------|------------|----------|
| Complex architecture | Over-engineering from the start | Start minimal, add complexity only when needed |
| Frontend/Backend API mismatch | No single source of truth | Define API contracts first, use TypeScript types generated from OpenAPI |
| CORS issues | Inconsistent configuration | Configure CORS once, correctly, at the start |
| Missing routes/endpoints | Poor planning | Document all endpoints before coding |
| Database model mismatches | Schema drift | Use Alembic migrations, never modify models without migration |
| Hard to deploy | Environment-specific code | Design for deployment from day 1 |

---

## Architecture Overview

### Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Backend | FastAPI (Python 3.11+) | Fast, modern, automatic OpenAPI docs |
| Frontend | Next.js 14 (App Router) | React with SSR, simple routing |
| Database | PostgreSQL | Reliable, well-supported |
| ORM | SQLAlchemy 2.0 | Mature, async support |
| Auth | JWT (python-jose) | Stateless, simple |
| Deployment | Render | Simple, reliable PaaS |

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    (Next.js on Render)                          │
│                                                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│   │  Login   │  │Dashboard │  │Customers │  │Facilities│       │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (REST API)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                   (FastAPI on Render)                           │
│                                                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│   │  /auth   │  │/customers│  │/facilities│  │  /stats  │       │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                              │                                   │
│                      ┌───────┴───────┐                          │
│                      │  SQLAlchemy   │                          │
│                      └───────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ PostgreSQL Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATABASE                                  │
│                 (PostgreSQL on Render)                          │
│                                                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│   │  users   │  │customers │  │facilities│                     │
│   └──────────┘  └──────────┘  └──────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

Keep it flat and simple. Avoid deep nesting.

```
banking-ops/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings (from env vars)
│   │   ├── database.py          # DB connection & session
│   │   │
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── customer.py
│   │   │   └── facility.py
│   │   │
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── customer.py
│   │   │   └── facility.py
│   │   │
│   │   ├── routers/             # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── customers.py
│   │   │   ├── facilities.py
│   │   │   └── stats.py
│   │   │
│   │   ├── services/            # Business logic (optional, for complex ops)
│   │   │   └── __init__.py
│   │   │
│   │   └── utils/               # Helpers
│   │       ├── __init__.py
│   │       └── security.py      # Password hashing, JWT
│   │
│   ├── alembic/                 # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_customers.py
│   │   └── test_facilities.py
│   │
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Redirect to /login or /dashboard
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   ├── customers/
│   │   │   │   ├── page.tsx     # List
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx # View/Edit
│   │   │   └── facilities/
│   │   │       ├── page.tsx
│   │   │       ├── new/
│   │   │       │   └── page.tsx
│   │   │       └── [id]/
│   │   │           └── page.tsx
│   │   │
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ui/              # Basic components (Button, Input, etc.)
│   │   │   ├── layout/          # Layout components (Sidebar, Header)
│   │   │   └── forms/           # Form components
│   │   │
│   │   ├── lib/                 # Utilities
│   │   │   ├── api.ts           # API client (fetch wrapper)
│   │   │   ├── auth.ts          # Auth helpers
│   │   │   └── utils.ts
│   │   │
│   │   └── types/               # TypeScript types
│   │       └── index.ts         # Match backend schemas exactly
│   │
│   ├── public/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── .env.example
│
├── render.yaml                  # Render Blueprint (IaC)
├── docker-compose.yml           # Local development
└── README.md
```

---

## Phase 1: Backend Foundation

**Duration**: 2-3 days
**Goal**: Working authentication and database setup

### 1.1 Project Setup

```bash
# Create project structure
mkdir -p backend/app/{models,schemas,routers,utils}
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg \
            python-jose[cryptography] passlib[bcrypt] python-dotenv \
            alembic pydantic-settings
pip freeze > requirements.txt
```

### 1.2 Configuration (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/banking"

    # JWT
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # App
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
```

### 1.3 Database Setup (database.py)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 1.4 User Model (models/user.py)

```python
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

### 1.5 User Schemas (schemas/user.py)

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Request schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Response schemas
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int | None = None
```

### 1.6 Security Utils (utils/security.py)

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user
```

### 1.7 Auth Router (routers/auth.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### 1.8 Main Application (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth

app = FastAPI(
    title="Banking Operations API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# CORS - Configure ONCE, correctly
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check (no auth required)
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(auth.router, prefix="/api")
```

### 1.9 Alembic Setup

```bash
# Initialize Alembic
alembic init alembic

# Edit alembic/env.py to use async and import models
# Edit alembic.ini to use DATABASE_URL from env

# Create first migration
alembic revision --autogenerate -m "Initial: users table"

# Run migration
alembic upgrade head
```

### Phase 1 Checklist

- [ ] Project structure created
- [ ] Dependencies installed
- [ ] Configuration loads from environment
- [ ] Database connection works
- [ ] User model created
- [ ] Alembic migration runs successfully
- [ ] Auth endpoints work:
  - [ ] POST /api/auth/register
  - [ ] POST /api/auth/login
  - [ ] GET /api/auth/me
- [ ] JWT authentication works
- [ ] Password hashing works
- [ ] CORS configured correctly

---

## Phase 2: Core API Endpoints

**Duration**: 3-4 days
**Goal**: Complete CRUD for customers and facilities

### 2.1 Customer Model (models/customer.py)

```python
from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.database import Base

class CustomerType(str, enum.Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    customer_type: Mapped[CustomerType] = mapped_column(Enum(CustomerType))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit fields
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    facilities: Mapped[list["Facility"]] = relationship(back_populates="customer")
```

### 2.2 Facility Model (models/facility.py)

```python
from sqlalchemy import String, Numeric, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from decimal import Decimal
import enum

from app.database import Base

class FacilityType(str, enum.Enum):
    TERM_LOAN = "term_loan"
    REVOLVING_CREDIT = "revolving_credit"
    OVERDRAFT = "overdraft"
    LETTER_OF_CREDIT = "letter_of_credit"

class FacilityStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    DEFAULT = "default"

class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    facility_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))

    facility_type: Mapped[FacilityType] = mapped_column(Enum(FacilityType))
    status: Mapped[FacilityStatus] = mapped_column(Enum(FacilityStatus), default=FacilityStatus.PENDING)

    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    start_date: Mapped[date] = mapped_column(Date)
    expiry_date: Mapped[date] = mapped_column(Date)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit fields
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="facilities")
```

### 2.3 Customer Schemas (schemas/customer.py)

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum

class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"

# Request schemas
class CustomerCreate(BaseModel):
    name: str
    customer_type: CustomerType
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

class CustomerUpdate(BaseModel):
    name: str | None = None
    customer_type: CustomerType | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

# Response schemas
class CustomerResponse(BaseModel):
    id: int
    name: str
    customer_type: CustomerType
    email: str | None
    phone: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int
    pages: int
```

### 2.4 Facility Schemas (schemas/facility.py)

```python
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class FacilityType(str, Enum):
    TERM_LOAN = "term_loan"
    REVOLVING_CREDIT = "revolving_credit"
    OVERDRAFT = "overdraft"
    LETTER_OF_CREDIT = "letter_of_credit"

class FacilityStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    DEFAULT = "default"

# Request schemas
class FacilityCreate(BaseModel):
    customer_id: int
    facility_type: FacilityType
    amount: Decimal
    currency: str = "USD"
    interest_rate: Decimal
    start_date: date
    expiry_date: date
    description: str | None = None

class FacilityUpdate(BaseModel):
    facility_type: FacilityType | None = None
    status: FacilityStatus | None = None
    amount: Decimal | None = None
    currency: str | None = None
    interest_rate: Decimal | None = None
    start_date: date | None = None
    expiry_date: date | None = None
    description: str | None = None

# Response schemas
class FacilityResponse(BaseModel):
    id: int
    facility_number: str
    customer_id: int
    facility_type: FacilityType
    status: FacilityStatus
    amount: Decimal
    currency: str
    interest_rate: Decimal
    start_date: date
    expiry_date: date
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FacilityListResponse(BaseModel):
    items: list[FacilityResponse]
    total: int
    page: int
    page_size: int
    pages: int
```

### 2.5 Customer Router (routers/customers.py)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Base query
    query = select(Customer)
    count_query = select(func.count(Customer.id))

    # Search filter
    if search:
        search_filter = Customer.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total = await db.scalar(count_query)

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Customer.created_at.desc())

    result = await db.execute(query)
    customers = result.scalars().all()

    return CustomerListResponse(
        items=customers,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = Customer(
        **customer_data.model_dump(),
        created_by=current_user.id
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)
    return customer

@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await db.delete(customer)
    await db.commit()
```

### 2.6 Facility Router (routers/facilities.py)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.database import get_db
from app.models.facility import Facility
from app.models.customer import Customer
from app.models.user import User
from app.schemas.facility import FacilityCreate, FacilityUpdate, FacilityResponse, FacilityListResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/facilities", tags=["Facilities"])

def generate_facility_number() -> str:
    return f"FAC-{uuid.uuid4().hex[:8].upper()}"

@router.get("", response_model=FacilityListResponse)
async def list_facilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Facility)
    count_query = select(func.count(Facility.id))

    # Filters
    if customer_id:
        query = query.where(Facility.customer_id == customer_id)
        count_query = count_query.where(Facility.customer_id == customer_id)
    if status:
        query = query.where(Facility.status == status)
        count_query = count_query.where(Facility.status == status)

    total = await db.scalar(count_query)

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Facility.created_at.desc())

    result = await db.execute(query)
    facilities = result.scalars().all()

    return FacilityListResponse(
        items=facilities,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )

@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Facility).where(Facility.id == facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility

@router.post("", response_model=FacilityResponse, status_code=201)
async def create_facility(
    facility_data: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify customer exists
    result = await db.execute(select(Customer).where(Customer.id == facility_data.customer_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Customer not found")

    facility = Facility(
        **facility_data.model_dump(),
        facility_number=generate_facility_number(),
        created_by=current_user.id
    )
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    return facility

@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: int,
    facility_data: FacilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Facility).where(Facility.id == facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    update_data = facility_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(facility, field, value)

    await db.commit()
    await db.refresh(facility)
    return facility

@router.delete("/{facility_id}", status_code=204)
async def delete_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Facility).where(Facility.id == facility_id))
    facility = result.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    await db.delete(facility)
    await db.commit()
```

### 2.7 Stats Router (routers/stats.py)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.models.customer import Customer
from app.models.facility import Facility, FacilityStatus
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/stats", tags=["Statistics"])

class DashboardStats(BaseModel):
    total_customers: int
    total_facilities: int
    active_facilities: int
    total_exposure: Decimal
    facilities_by_status: dict[str, int]

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total customers
    total_customers = await db.scalar(select(func.count(Customer.id)))

    # Total facilities
    total_facilities = await db.scalar(select(func.count(Facility.id)))

    # Active facilities
    active_facilities = await db.scalar(
        select(func.count(Facility.id)).where(Facility.status == FacilityStatus.ACTIVE)
    )

    # Total exposure (sum of active facility amounts)
    total_exposure = await db.scalar(
        select(func.sum(Facility.amount)).where(Facility.status == FacilityStatus.ACTIVE)
    ) or Decimal("0")

    # Facilities by status
    status_query = select(Facility.status, func.count(Facility.id)).group_by(Facility.status)
    result = await db.execute(status_query)
    facilities_by_status = {row[0].value: row[1] for row in result}

    return DashboardStats(
        total_customers=total_customers or 0,
        total_facilities=total_facilities or 0,
        active_facilities=active_facilities or 0,
        total_exposure=total_exposure,
        facilities_by_status=facilities_by_status
    )
```

### 2.8 Update main.py to include new routers

```python
from app.routers import auth, customers, facilities, stats

# ... existing code ...

app.include_router(auth.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(facilities.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
```

### Phase 2 Checklist

- [ ] Customer model and migration created
- [ ] Facility model and migration created
- [ ] Customer endpoints work:
  - [ ] GET /api/customers (list with pagination)
  - [ ] GET /api/customers/{id}
  - [ ] POST /api/customers
  - [ ] PUT /api/customers/{id}
  - [ ] DELETE /api/customers/{id}
- [ ] Facility endpoints work:
  - [ ] GET /api/facilities (list with pagination)
  - [ ] GET /api/facilities/{id}
  - [ ] POST /api/facilities
  - [ ] PUT /api/facilities/{id}
  - [ ] DELETE /api/facilities/{id}
- [ ] Stats endpoint works:
  - [ ] GET /api/stats/dashboard
- [ ] All endpoints require authentication
- [ ] Pagination works correctly
- [ ] Search/filter works

---

## Phase 3: Frontend Implementation

**Duration**: 4-5 days
**Goal**: Working UI for all features

### 3.1 Project Setup

```bash
# Create Next.js project
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir

cd frontend

# Install dependencies
npm install axios react-hook-form @hookform/resolvers zod
npm install lucide-react clsx tailwind-merge
npm install -D @types/node
```

### 3.2 API Client (lib/api.ts)

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.setToken(null);
        window.location.href = '/login';
      }
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }

    // Handle empty responses (204 No Content)
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async logout() {
    this.setToken(null);
  }

  async getMe() {
    return this.request<User>('/auth/me');
  }

  // Customers
  async getCustomers(params: { page?: number; page_size?: number; search?: string } = {}) {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.search) searchParams.set('search', params.search);

    return this.request<CustomerListResponse>(`/customers?${searchParams}`);
  }

  async getCustomer(id: number) {
    return this.request<Customer>(`/customers/${id}`);
  }

  async createCustomer(data: CustomerCreate) {
    return this.request<Customer>('/customers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCustomer(id: number, data: CustomerUpdate) {
    return this.request<Customer>(`/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCustomer(id: number) {
    return this.request<void>(`/customers/${id}`, { method: 'DELETE' });
  }

  // Facilities
  async getFacilities(params: { page?: number; page_size?: number; customer_id?: number; status?: string } = {}) {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
    if (params.customer_id) searchParams.set('customer_id', params.customer_id.toString());
    if (params.status) searchParams.set('status', params.status);

    return this.request<FacilityListResponse>(`/facilities?${searchParams}`);
  }

  async getFacility(id: number) {
    return this.request<Facility>(`/facilities/${id}`);
  }

  async createFacility(data: FacilityCreate) {
    return this.request<Facility>('/facilities', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateFacility(id: number, data: FacilityUpdate) {
    return this.request<Facility>(`/facilities/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteFacility(id: number) {
    return this.request<void>(`/facilities/${id}`, { method: 'DELETE' });
  }

  // Stats
  async getDashboardStats() {
    return this.request<DashboardStats>('/stats/dashboard');
  }
}

export const api = new ApiClient();
```

### 3.3 Types (types/index.ts)

```typescript
// User types
export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

// Customer types
export type CustomerType = 'individual' | 'corporate';

export interface Customer {
  id: number;
  name: string;
  customer_type: CustomerType;
  email: string | null;
  phone: string | null;
  address: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  name: string;
  customer_type: CustomerType;
  email?: string;
  phone?: string;
  address?: string;
}

export interface CustomerUpdate {
  name?: string;
  customer_type?: CustomerType;
  email?: string;
  phone?: string;
  address?: string;
}

export interface CustomerListResponse {
  items: Customer[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// Facility types
export type FacilityType = 'term_loan' | 'revolving_credit' | 'overdraft' | 'letter_of_credit';
export type FacilityStatus = 'pending' | 'active' | 'closed' | 'default';

export interface Facility {
  id: number;
  facility_number: string;
  customer_id: number;
  facility_type: FacilityType;
  status: FacilityStatus;
  amount: number;
  currency: string;
  interest_rate: number;
  start_date: string;
  expiry_date: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface FacilityCreate {
  customer_id: number;
  facility_type: FacilityType;
  amount: number;
  currency?: string;
  interest_rate: number;
  start_date: string;
  expiry_date: string;
  description?: string;
}

export interface FacilityUpdate {
  facility_type?: FacilityType;
  status?: FacilityStatus;
  amount?: number;
  currency?: string;
  interest_rate?: number;
  start_date?: string;
  expiry_date?: string;
  description?: string;
}

export interface FacilityListResponse {
  items: Facility[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// Stats types
export interface DashboardStats {
  total_customers: number;
  total_facilities: number;
  active_facilities: number;
  total_exposure: number;
  facilities_by_status: Record<string, number>;
}
```

### 3.4 Auth Context (lib/auth.tsx)

```typescript
'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { api } from './api';
import { User } from '@/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = api.getToken();
    if (token) {
      api.getMe()
        .then(setUser)
        .catch(() => api.setToken(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    await api.login(email, password);
    const user = await api.getMe();
    setUser(user);
    router.push('/dashboard');
  };

  const logout = () => {
    api.logout();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 3.5 Login Page (app/login/page.tsx)

```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">Banking Operations</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-500 p-3 rounded">{error}</div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
```

### 3.6 Dashboard Page (app/dashboard/page.tsx)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { DashboardStats } from '@/types';
import { useAuth } from '@/lib/auth';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    api.getDashboardStats()
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <p className="text-gray-600 mb-8">Welcome back, {user?.full_name}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Customers"
          value={stats?.total_customers || 0}
          color="blue"
        />
        <StatCard
          title="Total Facilities"
          value={stats?.total_facilities || 0}
          color="green"
        />
        <StatCard
          title="Active Facilities"
          value={stats?.active_facilities || 0}
          color="yellow"
        />
        <StatCard
          title="Total Exposure"
          value={`$${(stats?.total_exposure || 0).toLocaleString()}`}
          color="purple"
        />
      </div>

      {stats?.facilities_by_status && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Facilities by Status</h2>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.facilities_by_status).map(([status, count]) => (
                <div key={status} className="text-center">
                  <div className="text-2xl font-bold">{count}</div>
                  <div className="text-gray-500 capitalize">{status}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: string | number; color: string }) {
  const colors = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    purple: 'bg-purple-50 border-purple-200',
  };

  return (
    <div className={`p-6 rounded-lg border ${colors[color as keyof typeof colors]}`}>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-gray-600 mt-1">{title}</div>
    </div>
  );
}
```

### 3.7 Layout with Navigation (app/layout.tsx)

```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/auth';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Banking Operations',
  description: 'Banking Operations Management System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
```

### 3.8 Environment Configuration

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# frontend/.env.production
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api
```

### Phase 3 Checklist

- [ ] Next.js project created with TypeScript
- [ ] API client implemented and tested
- [ ] Types match backend schemas exactly
- [ ] Auth context works
- [ ] Login page:
  - [ ] Form validation
  - [ ] Error handling
  - [ ] Redirects after login
- [ ] Dashboard page:
  - [ ] Shows stats correctly
  - [ ] Responsive layout
- [ ] Customers pages:
  - [ ] List with pagination
  - [ ] Search functionality
  - [ ] Create form
  - [ ] Edit form
  - [ ] Delete with confirmation
- [ ] Facilities pages:
  - [ ] List with pagination
  - [ ] Filter by customer/status
  - [ ] Create form
  - [ ] Edit form
  - [ ] Delete with confirmation
- [ ] Protected routes redirect to login
- [ ] Logout works

---

## Phase 4: Deployment Configuration

**Duration**: 1-2 days
**Goal**: Deploy to Render with zero configuration changes

### 4.1 Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 4.2 Frontend Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

### 4.3 Frontend next.config.js (for standalone output)

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
};

module.exports = nextConfig;
```

### 4.4 Render Blueprint (render.yaml)

```yaml
# render.yaml - Infrastructure as Code
services:
  # Backend API
  - type: web
    name: banking-api
    env: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    healthCheckPath: /api/health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: banking-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: CORS_ORIGINS
        value: https://banking-web.onrender.com
      - key: DEBUG
        value: false

  # Frontend
  - type: web
    name: banking-web
    env: docker
    dockerfilePath: ./frontend/Dockerfile
    dockerContext: ./frontend
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: https://banking-api.onrender.com/api

databases:
  - name: banking-db
    databaseName: banking
    user: banking
    plan: free
```

### 4.5 Local Development (docker-compose.yml)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: banking
      POSTGRES_PASSWORD: banking
      POSTGRES_DB: banking
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://banking:banking@db:5432/banking
      SECRET_KEY: dev-secret-key
      CORS_ORIGINS: '["http://localhost:3000"]'
      DEBUG: "true"
    depends_on:
      - db
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 4.6 Environment Variables Reference

| Variable | Backend | Frontend | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | Yes | No | PostgreSQL connection string |
| `SECRET_KEY` | Yes | No | JWT signing key |
| `CORS_ORIGINS` | Yes | No | Allowed frontend origins |
| `DEBUG` | Yes | No | Enable debug mode |
| `NEXT_PUBLIC_API_URL` | No | Yes | Backend API URL |

### Phase 4 Checklist

- [ ] Backend Dockerfile works
- [ ] Frontend Dockerfile works
- [ ] render.yaml is valid
- [ ] docker-compose works locally
- [ ] Environment variables documented
- [ ] Health check endpoint works
- [ ] Migrations run on startup
- [ ] CORS configured correctly for production
- [ ] No hardcoded URLs

---

## Phase 5: Optional Features

**Duration**: As needed
**Goal**: Enhance the system after core functionality is stable

### 5.1 AI Integration

Add AI-powered features after the core system is working:

```python
# backend/app/routers/ai.py
from fastapi import APIRouter, Depends
from openai import AsyncOpenAI

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/analyze-customer")
async def analyze_customer(customer_id: int):
    """AI-powered customer risk analysis"""
    # Fetch customer and facility data
    # Send to OpenAI for analysis
    # Return insights
    pass

@router.post("/chat")
async def chat(message: str):
    """AI chatbot for queries"""
    pass
```

**AI Features to Consider:**
- Customer risk scoring
- Facility recommendation engine
- Natural language queries
- Document analysis
- Anomaly detection

### 5.2 Reports and Exports

```python
# backend/app/routers/reports.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import csv
import io

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/customers/export")
async def export_customers():
    """Export customers to CSV"""
    pass

@router.get("/facilities/export")
async def export_facilities():
    """Export facilities to CSV"""
    pass

@router.get("/portfolio-summary")
async def portfolio_summary():
    """Generate portfolio summary report"""
    pass
```

### 5.3 Audit Logging

```python
# backend/app/models/audit.py
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str]  # CREATE, UPDATE, DELETE
    entity_type: Mapped[str]  # Customer, Facility
    entity_id: Mapped[int]
    changes: Mapped[dict]  # JSON of changes
    timestamp: Mapped[datetime]
```

### 5.4 Notifications

```python
# backend/app/services/notifications.py
class NotificationService:
    async def send_email(self, to: str, subject: str, body: str):
        pass

    async def notify_facility_expiring(self, facility_id: int):
        pass
```

### 5.5 Role-Based Access Control

```python
# backend/app/models/role.py
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]  # admin, manager, analyst
    permissions: Mapped[list[str]]  # JSON array

# backend/app/utils/security.py
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if permission not in current_user.role.permissions:
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### Phase 5 Checklist

- [ ] AI integration (if needed)
  - [ ] OpenAI client setup
  - [ ] Risk analysis endpoint
  - [ ] Chat endpoint
- [ ] Reports
  - [ ] CSV export
  - [ ] PDF reports
- [ ] Audit logging
  - [ ] Model created
  - [ ] Middleware added
  - [ ] Logs viewable
- [ ] Notifications
  - [ ] Email service
  - [ ] Expiry alerts
- [ ] RBAC
  - [ ] Role model
  - [ ] Permission checks
  - [ ] UI adjustments

---

## Testing Strategy

### Backend Testing

```python
# backend/tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def authenticated_client(client):
    # Create user and login
    # Return client with auth header
    pass
```

```python
# backend/tests/test_customers.py
import pytest

@pytest.mark.asyncio
async def test_create_customer(authenticated_client):
    response = await authenticated_client.post("/api/customers", json={
        "name": "Test Customer",
        "customer_type": "individual"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Test Customer"
```

### Frontend Testing

```typescript
// frontend/__tests__/api.test.ts
import { api } from '@/lib/api';

describe('API Client', () => {
  it('should login successfully', async () => {
    // Mock fetch
    // Test login
  });
});
```

---

## Checklist

### Pre-Development

- [ ] Database design reviewed
- [ ] API endpoints documented
- [ ] Frontend wireframes approved
- [ ] Environment variables listed

### Phase 1 Complete

- [ ] Auth working
- [ ] Database connected
- [ ] Migrations run
- [ ] CORS configured

### Phase 2 Complete

- [ ] All CRUD endpoints work
- [ ] Pagination works
- [ ] Search works
- [ ] Stats endpoint works

### Phase 3 Complete

- [ ] Login works
- [ ] Dashboard shows data
- [ ] Customers CRUD works
- [ ] Facilities CRUD works
- [ ] Responsive on mobile

### Phase 4 Complete

- [ ] Deployed to Render
- [ ] No errors in logs
- [ ] Frontend can reach backend
- [ ] Database migrations ran

### Production Ready

- [ ] All tests pass
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Security reviewed
- [ ] Documentation complete

---

## Quick Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register user |
| POST | /api/auth/login | Login (returns JWT) |
| GET | /api/auth/me | Get current user |
| GET | /api/customers | List customers |
| POST | /api/customers | Create customer |
| GET | /api/customers/{id} | Get customer |
| PUT | /api/customers/{id} | Update customer |
| DELETE | /api/customers/{id} | Delete customer |
| GET | /api/facilities | List facilities |
| POST | /api/facilities | Create facility |
| GET | /api/facilities/{id} | Get facility |
| PUT | /api/facilities/{id} | Update facility |
| DELETE | /api/facilities/{id} | Delete facility |
| GET | /api/stats/dashboard | Get dashboard stats |
| GET | /api/health | Health check |

### Common Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload          # Run dev server
alembic revision --autogenerate -m ""  # Create migration
alembic upgrade head                    # Run migrations
pytest                                  # Run tests

# Frontend
cd frontend
npm run dev                             # Run dev server
npm run build                           # Build for production
npm run lint                            # Lint code

# Docker
docker-compose up -d                    # Start all services
docker-compose logs -f backend          # View backend logs
docker-compose down                     # Stop all services

# Render
render blueprint apply                  # Deploy using render.yaml
```

---

## Principles to Remember

1. **Start simple, add complexity later** - Don't optimize prematurely
2. **Test each phase before moving on** - Don't build on broken foundations
3. **Keep frontend and backend types in sync** - Mismatches cause bugs
4. **Configure for deployment from day 1** - Avoid "works on my machine"
5. **Document as you go** - Future you will thank present you
6. **Use environment variables** - Never hardcode configuration
7. **Handle errors gracefully** - Users shouldn't see stack traces
8. **Log meaningful information** - But not sensitive data

---

*Last Updated: January 2026*
