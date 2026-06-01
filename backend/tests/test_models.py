"""Tests for database models"""
import pytest
from datetime import datetime, date
from decimal import Decimal

from app.models.user import User, generate_id
from app.models.customer import Customer, AccountType, CustomerStatus, generate_customer_id
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.utils.security import hash_password


class TestUserModel:
    """Test User model"""
    
    def test_generate_id(self):
        """Test user ID generation"""
        user_id = generate_id()
        assert len(user_id) == 8
        assert user_id.isalnum()
        
        # Test uniqueness
        user_id2 = generate_id()
        assert user_id != user_id2
    
    def test_user_creation(self):
        """Test user model creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.hashed_password != "password123"  # Should be hashed
        assert len(user.hashed_password) > 20  # Hashed password is longer
    
    def test_user_defaults(self):
        """Test user model defaults"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        
        assert user.is_active is True
        assert user.is_admin is False
        assert user.full_name is None
        assert user.last_login is None


class TestCustomerModel:
    """Test Customer model"""
    
    def test_generate_customer_id(self):
        """Test customer ID generation"""
        customer_id = generate_customer_id()
        assert customer_id.startswith("C")
        assert len(customer_id) == 33  # C + 32 chars
        
        # Test uniqueness
        customer_id2 = generate_customer_id()
        assert customer_id != customer_id2
    
    def test_customer_creation(self):
        """Test customer model creation"""
        customer = Customer(
            account_no="ACC001",
            name="Test Customer",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE,
            email="customer@test.com",
            phone="1234567890",
            branch="Main Branch"
        )
        
        assert customer.account_no == "ACC001"
        assert customer.name == "Test Customer"
        assert customer.account_type == AccountType.RETAIL
        assert customer.status == CustomerStatus.ACTIVE
        assert customer.email == "customer@test.com"
        assert customer.phone == "1234567890"
        assert customer.branch == "Main Branch"
        assert customer.is_deleted is False
    
    def test_customer_defaults(self):
        """Test customer model defaults"""
        customer = Customer(
            account_no="ACC001",
            name="Test Customer"
        )
        
        assert customer.account_type == AccountType.RETAIL
        assert customer.status == CustomerStatus.ACTIVE
        assert customer.is_deleted is False
        assert customer.name_ar is None
        assert customer.email is None
        assert customer.phone is None
        assert customer.mobile is None
        assert customer.address is None
        assert customer.branch is None
        assert customer.relationship_manager is None
        assert customer.notes is None
    
    def test_account_type_enum(self):
        """Test AccountType enum values"""
        assert AccountType.RETAIL == "retail"
        assert AccountType.CORPORATE == "corporate"
        assert AccountType.SME == "sme"
    
    def test_customer_status_enum(self):
        """Test CustomerStatus enum values"""
        assert CustomerStatus.ACTIVE == "active"
        assert CustomerStatus.INACTIVE == "inactive"
        assert CustomerStatus.SUSPENDED == "suspended"


class TestFacilityModel:
    """Test Facility model"""
    
    def test_facility_creation(self):
        """Test facility model creation"""
        facility = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.LOAN,
            name="Test Loan",
            amount=Decimal("100000.00"),
            outstanding=Decimal("50000.00"),
            currency="AED",
            start_date=date(2024, 1, 1),
            expiry_date=date(2024, 12, 31),
            interest_rate=Decimal("5.5"),
            tenor_months="12"
        )
        
        assert facility.customer_id == "C12345678"
        assert facility.facility_type == FacilityType.LOAN
        assert facility.name == "Test Loan"
        assert facility.amount == Decimal("100000.00")
        assert facility.outstanding == Decimal("50000.00")
        assert facility.currency == "AED"
        assert facility.start_date == date(2024, 1, 1)
        assert facility.expiry_date == date(2024, 12, 31)
        assert facility.interest_rate == Decimal("5.5")
        assert facility.tenor_months == "12"
        assert facility.status == FacilityStatus.ACTIVE
        assert facility.is_deleted is False
    
    def test_facility_defaults(self):
        """Test facility model defaults"""
        facility = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.LOAN,
            amount=Decimal("100000.00")
        )
        
        assert facility.status == FacilityStatus.ACTIVE
        assert facility.outstanding == 0
        assert facility.currency == "AED"
        assert facility.is_deleted is False
        assert facility.name is None
        assert facility.start_date is None
        assert facility.expiry_date is None
        assert facility.interest_rate is None
        assert facility.tenor_months is None
        assert facility.notes is None
    
    def test_facility_type_enum(self):
        """Test FacilityType enum values"""
        assert FacilityType.LOAN == "loan"
        assert FacilityType.OVERDRAFT == "overdraft"
        assert FacilityType.LC == "lc"
        assert FacilityType.LG == "lg"
        assert FacilityType.OTHER == "other"
    
    def test_facility_status_enum(self):
        """Test FacilityStatus enum values"""
        assert FacilityStatus.ACTIVE == "active"
        assert FacilityStatus.PENDING == "pending"
        assert FacilityStatus.CLOSED == "closed"
        assert FacilityStatus.DEFAULTED == "defaulted"
    
    def test_facility_repr(self):
        """Test facility string representation"""
        facility = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.LOAN,
            amount=Decimal("100000.00"),
            currency="USD",
            status=FacilityStatus.ACTIVE
        )
        
        repr_str = repr(facility)
        assert "Facility" in repr_str
        assert "C12345678" in repr_str
        assert "loan" in repr_str
        assert "100000" in repr_str
        assert "USD" in repr_str
        assert "active" in repr_str
    
    def test_facility_str(self):
        """Test facility human-readable string"""
        facility = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.LOAN,
            name="Personal Loan"
        )
        facility.id = "F1234567"
        
        str_repr = str(facility)
        assert "Facility F1234567" in str_repr
        assert "loan" in str_repr
        assert "Personal Loan" in str_repr
        
        # Test without name
        facility_no_name = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.OVERDRAFT
        )
        facility_no_name.id = "F7654321"
        
        str_repr_no_name = str(facility_no_name)
        assert "Facility F7654321" in str_repr_no_name
        assert "overdraft" in str_repr_no_name
        assert "Personal Loan" not in str_repr_no_name


class TestModelRelationships:
    """Test model relationships"""
    
    def test_customer_facility_relationship(self):
        """Test customer-facility relationship"""
        customer = Customer(
            account_no="ACC001",
            name="Test Customer"
        )
        customer.id = "C12345678"
        
        facility = Facility(
            customer_id=customer.id,
            facility_type=FacilityType.LOAN,
            amount=Decimal("100000.00")
        )
        
        # Test that customer_id matches
        assert facility.customer_id == customer.id
        
        # Note: Actual relationship testing would require database session
        # which is covered in integration tests


class TestModelValidation:
    """Test model validation and constraints"""
    
    def test_customer_required_fields(self):
        """Test customer required fields"""
        # Should not raise exception with required fields
        customer = Customer(
            account_no="ACC001",
            name="Test Customer"
        )
        assert customer.account_no == "ACC001"
        assert customer.name == "Test Customer"
    
    def test_facility_required_fields(self):
        """Test facility required fields"""
        # Should not raise exception with required fields
        facility = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.LOAN,
            amount=Decimal("100000.00")
        )
        assert facility.customer_id == "C12345678"
        assert facility.facility_type == FacilityType.LOAN
        assert facility.amount == Decimal("100000.00")
    
    def test_risk_rating_is_validated(self):
        """risk_rating is constrained to the RiskRating set by @validates."""
        from app.models.facility import RiskRating

        # Accepts and normalises case + enum members.
        assert Facility(customer_id="C1", amount=Decimal("1"), risk_rating="HIGH").risk_rating == "high"
        assert Facility(customer_id="C1", amount=Decimal("1"), risk_rating="Medium").risk_rating == "medium"
        assert Facility(customer_id="C1", amount=Decimal("1"), risk_rating=RiskRating.HIGH).risk_rating == "high"
        # Blank / None fall back to the default rather than violating NOT NULL.
        assert Facility(customer_id="C1", amount=Decimal("1"), risk_rating="").risk_rating == "low"
        assert Facility(customer_id="C1", amount=Decimal("1"), risk_rating=None).risk_rating == "low"
        # An out-of-range value is rejected at write time.
        with pytest.raises(ValueError):
            Facility(customer_id="C1", amount=Decimal("1"), risk_rating="extreme")

    def test_decimal_precision(self):
        """Test decimal field precision"""
        facility = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.LOAN,
            amount=Decimal("123456.78"),
            outstanding=Decimal("54321.99"),
            interest_rate=Decimal("12.345")
        )

        assert facility.amount == Decimal("123456.78")
        assert facility.outstanding == Decimal("54321.99")
        assert facility.interest_rate == Decimal("12.345")
    
    def test_date_fields(self):
        """Test date field handling"""
        test_date = date(2024, 6, 15)
        facility = Facility(
            customer_id="C12345678",
            facility_type=FacilityType.LOAN,
            amount=Decimal("100000.00"),
            start_date=test_date,
            expiry_date=test_date
        )
        
        assert facility.start_date == test_date
        assert facility.expiry_date == test_date
        assert isinstance(facility.start_date, date)
        assert isinstance(facility.expiry_date, date)