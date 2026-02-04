"""
Test package for ALLIN1 Banking System

This package contains comprehensive tests for:
- Unit tests for models, schemas, and utilities
- Integration tests for API endpoints
- Authentication and authorization tests
- Database and migration tests
- Performance and load tests
"""

__version__ = "1.0.0"

# Test configuration constants
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SECRET_KEY = "test-secret-key-for-testing-only-not-for-production-use"
TEST_ALGORITHM = "HS256"
TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Test data constants
TEST_USERS = {
    "admin": {
        "username": "testadmin",
        "email": "admin@test.com",
        "password": "admin123!",
        "full_name": "Test Admin",
        "is_admin": True
    },
    "user": {
        "username": "testuser",
        "email": "user@test.com", 
        "password": "user123!",
        "full_name": "Test User",
        "is_admin": False
    }
}

TEST_CUSTOMERS = {
    "retail": {
        "account_no": "RET001",
        "name": "John Doe",
        "account_type": "retail",
        "email": "john@example.com",
        "phone": "+971501234567"
    },
    "corporate": {
        "account_no": "CORP001", 
        "name": "ABC Corporation",
        "account_type": "corporate",
        "email": "contact@abc.com",
        "phone": "+971507654321"
    }
}

TEST_FACILITIES = {
    "loan": {
        "facility_type": "loan",
        "name": "Personal Loan",
        "amount": 100000.00,
        "currency": "AED",
        "interest_rate": 5.5
    },
    "overdraft": {
        "facility_type": "overdraft",
        "name": "Overdraft Facility",
        "amount": 50000.00,
        "currency": "AED", 
        "interest_rate": 8.0
    }
}