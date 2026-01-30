```python
"""Tests for facility endpoints"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime

from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.user import User


class TestFacilityEndpoints:
    """Test facility CRUD endpoints"""

    async def test_get_facilities_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting facilities when none exist"""
        response = await client.get("/api/facilities/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1

    async def test_get_facilities_with_data(self, client: AsyncClient, auth_headers: dict, test_facility: Facility):
        """Test getting facilities with existing data"""
        response = await client.get("/api/facilities/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        facility = data["items"][0]
        assert facility["id"] == test_facility.id
        assert facility["facility_type"] == test_facility.facility_type.value
        assert float(facility["amount"]) == float(test_facility.amount)

    async def test_get_facilities_pagination(self, client: AsyncClient, auth_headers: dict, test_customer: Customer, db_session: AsyncSession):
        """Test facility pagination"""
        # Create multiple facilities
        for i in range(5):
            facility = Facility(
                customer_id=test_customer.id,
                facility_type=FacilityType.LOAN,
                name=f"Facility {i}",
                amount=10000 + (i * 1000),
                currency="AED",
                status=FacilityStatus.ACTIVE
            )
            db_session.add(facility)
        await db_session.commit()

        # Test first page
        response = await client.get("/api/facilities/?page=1&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        assert data["page"] == 1

        # Test second page
        response = await client.get("/api/facilities/?page=2&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    async def test_get_facilities_filter_by_customer(self, client: AsyncClient, auth_headers: dict, test_customer: Customer, test_facility: Facility, db_session: AsyncSession):
        """Test filtering facilities by customer"""
        # Create another customer and facility
        another_customer = Customer(
            account_no="CUST999",
            name="Another Customer",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE
        )
        db_session.add(another_customer)
        await db_session.commit()
        await db_session.refresh(another_customer)

        another_facility = Facility(
            customer_id=another_customer.id,
            facility_type=FacilityType.OVERDRAFT,
            amount=5000,
            currency="AED",
            status=FacilityStatus.ACTIVE
        )
        db_session.add(another_facility)
        await db_session.commit()

        # Filter by customer
        response = await client.get(f"/api/facilities/?customer_id={test_customer.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["customer_id"] == test_customer.id

    async def test_get_facilities_filter_by_type(self, client: AsyncClient, auth_headers: dict, test_customer: Customer, db_session: AsyncSession):
        """Test filtering facilities by type"""
        # Create facilities with different types
        loan_facility = Facility(
            customer_id=test_customer.id,
            facility_type=FacilityType.LOAN,
            amount=50000,
            currency="AED",
            status=FacilityStatus.ACTIVE
        )
        overdraft_facility = Facility(
            customer_id=test_customer.id,
            facility_type=FacilityType.OVERDRAFT,
            amount=10000,
            currency="AED",
            status=FacilityStatus.ACTIVE
        )
        
        db_session.add_all([loan_facility, overdraft_facility])
        await db_session.commit()

        # Filter by loan
        response = await client.get("/api/facilities/?facility_type=loan", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["facility_type"] == "loan"

        # Filter by overdraft
        response = await client.get("/api/facilities/?facility_type=overdraft", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["facility_type"] == "overdraft"

    async def test_get_facility_by_id(self, client: AsyncClient, auth_headers: dict, test_facility: Facility):
        """Test getting a specific facility by ID"""
        response = await client.get(f"/api/facilities/{test_facility.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_facility.id
        assert data["customer_id"] == test_facility.customer_id
        assert data["facility_type"] == test_facility.facility_type.value
        assert float(data["amount"]) == float(test_facility.amount)

    async def test_get_facility_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent facility"""
        response = await client.get("/api/facilities/NONEXISTENT", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Facility not found" in response.json()["detail"]

    async def test_create_facility_success(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test successful facility creation"""
        facility_data = {
            "customer_id": test_customer.id,
            "facility_type": "loan",
            "name": "New Loan Facility",
            "amount": 75000.00,
            "currency": "AED",
            "start_date": "2024-01-01",
            "expiry_date": "2024-12-31",
            "interest_rate": 6.5,
            "tenor_months": "12",
            "notes": "Test facility"
        }
        
        response = await client.post("/api/facilities/", json=facility_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == facility_data["customer_id"]
        assert data["facility_type"] == facility_data["facility_type"]
        assert data["name"] == facility_data["name"]
        assert float(data["amount"]) == facility_data["amount"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_facility_customer_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test creating facility with non-existent customer"""
        facility_data = {
            "customer_id": "NONEXISTENT",
            "facility_type": "loan",
            "amount": 50000.00,
            "currency": "AED"
        }
        
        response = await client.post("/api/facilities/", json=facility_data, headers=auth_headers)
        
        assert response.status_code == 404
        assert "Customer not found" in response.json()["detail"]

    async def test_create_facility_invalid_data(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test creating facility with invalid data"""
        # Missing required fields
        facility_data = {
            "customer_id": test_customer.id,
            "facility_type": "loan"
            # Missing amount
        }
        
        response = await client.post("/api/facilities/", json=facility_data, headers=auth_headers)
        
        assert response.status_code == 422

        # Invalid amount
        facility_data = {
            "customer_id": test_customer.id,
            "facility_type": "loan",
            "amount": -1000  # Negative amount
        }
        
        response = await client.post("/api/facilities/", json=facility_data, headers=auth_headers)
        
        assert response.status_code == 422

    async def test_update_facility_success(self, client: AsyncClient, auth_headers: dict, test_facility: Facility):
        """Test successful facility update"""
        update_data = {
            "name": "Updated Facility Name",
            "amount": 120000.00,
            "interest_rate": 7.0,
            "notes": "Updated notes"
        }
        
        response = await client.put(f"/api/facilities/{test_facility.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert float(data["amount"]) == update_data["amount"]
        assert float(data["interest_rate"]) == update_data["interest_rate"]
        assert data["notes"] == update_data["notes"]

    async def test_update_facility_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test updating non-existent facility"""
        update_data = {"name": "Updated Name"}
        
        response = await client.put("/api/facilities/NONEXISTENT", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404

    async def test_delete_facility_success(self, client: AsyncClient, auth_headers: dict, test_facility: Facility):
        """Test successful facility deletion (soft delete)"""
        response = await client.delete(f"/api/facilities/{test_facility.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify facility is soft deleted
        get_response = await client.get(f"/api/facilities/{test_facility.id}", headers=auth_headers)
        assert get_response.status_code == 404

    async def test_delete_facility_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent facility"""
        response = await client.delete("/api/facilities/NONEXISTENT", headers=auth_headers)
        
        assert response.status_code == 404

    async def test_restore_facility_success(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_customer: Customer):
        """Test restoring a soft-deleted facility"""
        # Create and soft delete a facility
        facility = Facility(
            customer_id=test_customer.id,
            facility_type=FacilityType.LOAN,
            amount=25000,
            currency="AED",
            status=FacilityStatus.CLOSED,
            is_deleted=True
        )
        db_session.add(facility)
        await db_session.commit()
        await db_session.refresh(facility)
        
        response = await client.post(f"/api/facilities/{facility.id}/restore", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == facility.id
        assert data["status"] == "active"

    async def test_restore_facility_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test restoring non-existent deleted facility"""
        response = await client.post("/api/facilities/NONEXISTENT/restore", headers=auth_headers)
        
        assert response.status_code == 404

    async def test_update_facility_status(self, client: AsyncClient, auth_headers: dict, test_facility: Facility):
        """Test updating facility status"""
        response = await client.patch(f"/api/facilities/{test_facility.id}/status?new_status=closed", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Facility status updated to closed" in data["message"]

    async def test_advanced_search_facilities(self, client: AsyncClient, auth_headers: dict, test_customer: Customer, db_session: AsyncSession):
        """Test advanced facility search"""
        # Create facilities with different attributes
        facilities_data = [
            {"amount": 10000, "start_date": date(2024, 1, 1), "expiry_date": date(2024, 6, 30)},
            {"amount": 50000, "start_date": date(2024, 2, 1), "expiry_date": date(2024, 12, 31)},
            {"amount": 25000, "start_date": date(2024, 3, 1), "expiry_date": date(2025, 3, 1)},
        ]
        
        for i, data in enumerate(facilities_data):
            facility = Facility(
                customer_id=test_customer.id,
                facility_type=FacilityType.LOAN,
                name=f"Search Facility {i}",
                amount=data["amount"],
                currency="AED",
                start_date=data["start_date"],
                expiry_date=data["expiry_date"],
                status=FacilityStatus.ACTIVE
            )
            db_session.add(facility)
        await db_session.commit()

        # Search by amount range
        response = await client.get("/api/facilities/search/advanced?amount_from=20000&amount_to=60000", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

        # Search by date range
        response = await client.get("/api/facilities/search/advanced?date_from=2024-02-01&date_to=2024-03-31", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

        # Search by customer name
        response = await client.get(f"/api/facilities/search/advanced?customer_name={test_customer.name}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3

    # Authorization tests for different user roles
    async def test_facilities_unauthorized(self, client: AsyncClient):
        """Test accessing facilities without authentication"""
        response = await client.get("/api/facilities/")
        assert response.status_code == 401
        
        response = await client.post("/api/facilities/", json={"customer_id": "TEST", "facility_type": "loan", "amount": 1000})
        assert response.status_code == 401
        
        response = await client.put("/api/facilities/TEST123", json={"amount": 2000})
        assert response.status_code == 401
        
        response = await client.delete("/api/facilities/TEST123")
        assert response.status_code == 401

    async def test_regular_user_can_read_facilities(self, client: AsyncClient, auth_headers: dict, test_facility: Facility):
        """Test regular user can read facilities"""
        # Regular user should be able to read facilities
        response = await client.get("/api/facilities/", headers