"""Tests for customer endpoints"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.customer import Customer, AccountType, CustomerStatus


class TestCustomerEndpoints:
    """Test customer CRUD endpoints"""

    async def test_get_customers_empty(self, client: AsyncClient, auth_headers: dict):
        """Test getting customers when none exist"""
        response = await client.get("/api/customers/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1

    async def test_get_customers_with_data(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test getting customers with existing data"""
        response = await client.get("/api/customers/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["account_no"] == test_customer.account_no
        assert data["items"][0]["name"] == test_customer.name

    async def test_get_customers_pagination(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test customer pagination"""
        # Create multiple customers
        for i in range(5):
            customer = Customer(
                account_no=f"ACC{i:03d}",
                name=f"Customer {i}",
                account_type=AccountType.RETAIL,
                status=CustomerStatus.ACTIVE
            )
            db_session.add(customer)
        await db_session.commit()

        # Test first page
        response = await client.get("/api/customers/?page=1&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        assert data["page"] == 1

        # Test second page
        response = await client.get("/api/customers/?page=2&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    async def test_get_customers_search(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test customer search functionality"""
        # Create customers with different names
        customers_data = [
            ("ACC001", "John Doe", "john@example.com"),
            ("ACC002", "Jane Smith", "jane@example.com"),
            ("ACC003", "Bob Johnson", "bob@example.com"),
        ]
        
        for account_no, name, email in customers_data:
            customer = Customer(
                account_no=account_no,
                name=name,
                email=email,
                account_type=AccountType.RETAIL,
                status=CustomerStatus.ACTIVE
            )
            db_session.add(customer)
        await db_session.commit()

        # Substring, case-insensitive search: 'John' matches "John Doe" AND
        # "Bob Johnson" (Johnson contains John).
        response = await client.get("/api/customers/?search=John", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        names = {c["name"] for c in data["items"]}
        assert "John Doe" in names and "Bob Johnson" in names

        # 'J' matches John Doe, Jane Smith and Bob Johnson (all contain 'j').
        response = await client.get("/api/customers/?search=J", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3

        # Search by account number
        response = await client.get("/api/customers/?search=ACC001", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["account_no"] == "ACC001"

        # Search by email
        response = await client.get("/api/customers/?search=jane@example.com", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["email"] == "jane@example.com"

    async def test_get_customers_filter_by_type(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test filtering customers by account type"""
        # Create customers with different types
        retail_customer = Customer(
            account_no="RET001",
            name="Retail Customer",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE
        )
        corporate_customer = Customer(
            account_no="CORP001",
            name="Corporate Customer",
            account_type=AccountType.CORPORATE,
            status=CustomerStatus.ACTIVE
        )
        
        db_session.add_all([retail_customer, corporate_customer])
        await db_session.commit()

        # Filter by retail
        response = await client.get("/api/customers/?account_type=retail", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["account_type"] == "retail"

        # Filter by corporate
        response = await client.get("/api/customers/?account_type=corporate", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["account_type"] == "corporate"

    async def test_get_customer_by_id(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test getting a specific customer by ID"""
        response = await client.get(f"/api/customers/{test_customer.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_customer.id
        assert data["account_no"] == test_customer.account_no
        assert data["name"] == test_customer.name

    async def test_get_customer_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent customer"""
        response = await client.get("/api/customers/NONEXISTENT", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Customer not found" in response.json()["detail"]

    async def test_create_customer_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful customer creation"""
        customer_data = {
            "account_no": "NEW001",
            "name": "New Customer",
            "account_type": "retail",
            "email": "new@example.com",
            "phone": "1234567890",
            "branch": "Main Branch",
            "notes": "Test customer"
        }
        
        response = await client.post("/api/customers/", json=customer_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["account_no"] == customer_data["account_no"]
        assert data["name"] == customer_data["name"]
        assert data["email"] == customer_data["email"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_customer_duplicate_account_no(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test creating customer with duplicate account number"""
        customer_data = {
            "account_no": test_customer.account_no,  # Duplicate
            "name": "Another Customer",
            "account_type": "retail"
        }
        
        response = await client.post("/api/customers/", json=customer_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Customer with this account number already exists" in response.json()["detail"]

    async def test_create_customer_invalid_data(self, client: AsyncClient, auth_headers: dict):
        """Test creating customer with invalid data"""
        # Missing required fields
        customer_data = {
            "name": "Test Customer"
            # Missing account_no
        }
        
        response = await client.post("/api/customers/", json=customer_data, headers=auth_headers)
        
        assert response.status_code == 422

    async def test_update_customer_success(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test successful customer update"""
        update_data = {
            "name": "Updated Customer Name",
            "email": "updated@example.com",
            "phone": "9876543210"
        }
        
        response = await client.put(f"/api/customers/{test_customer.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["email"] == update_data["email"]
        assert data["phone"] == update_data["phone"]
        assert data["account_no"] == test_customer.account_no  # Unchanged

    async def test_update_customer_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test updating non-existent customer"""
        update_data = {"name": "Updated Name"}
        
        response = await client.put("/api/customers/NONEXISTENT", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404

    async def test_update_customer_duplicate_account_no(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test updating customer with duplicate account number"""
        # Create two customers
        customer1 = Customer(
            account_no="CUST001",
            name="Customer 1",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE
        )
        customer2 = Customer(
            account_no="CUST002",
            name="Customer 2",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE
        )
        db_session.add_all([customer1, customer2])
        await db_session.commit()
        
        # Try to update customer2 with customer1's account number
        update_data = {"account_no": customer1.account_no}
        
        response = await client.put(f"/api/customers/{customer2.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Another customer with this account number already exists" in response.json()["detail"]

    async def test_delete_customer_success(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test successful customer deletion (soft delete)"""
        response = await client.delete(f"/api/customers/{test_customer.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify customer is soft deleted
        get_response = await client.get(f"/api/customers/{test_customer.id}", headers=auth_headers)
        assert get_response.status_code == 404

    async def test_delete_customer_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent customer"""
        response = await client.delete("/api/customers/NONEXISTENT", headers=auth_headers)
        
        assert response.status_code == 404

    async def test_restore_customer_success(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test restoring a soft-deleted customer"""
        # Create and soft delete a customer
        customer = Customer(
            account_no="RESTORE001",
            name="Restore Customer",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.INACTIVE,
            is_deleted=True
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        response = await client.post(f"/api/customers/{customer.id}/restore", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer.id
        assert data["status"] == "active"

    async def test_restore_customer_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test restoring non-existent deleted customer"""
        response = await client.post("/api/customers/NONEXISTENT/restore", headers=auth_headers)
        
        assert response.status_code == 404

    async def test_get_customer_facilities(self, client: AsyncClient, auth_headers: dict, test_customer: Customer, test_facility):
        """Test getting facilities for a customer"""
        response = await client.get(f"/api/customers/{test_customer.id}/facilities", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "customer" in data
        assert "facilities" in data
        assert data["customer"]["id"] == test_customer.id
        assert data["total_facilities"] == 1

    async def test_get_customers_summary(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test getting customer statistics summary"""
        response = await client.get("/api/customers/stats/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "active" in data
        assert "by_type" in data
        assert "by_status" in data
        assert data["total"] >= 1

    async def test_customers_unauthorized(self, client: AsyncClient):
        """Test accessing customers without authentication"""
        response = await client.get("/api/customers/")
        assert response.status_code == 401
        
        response = await client.post("/api/customers/", json={"account_no": "TEST", "name": "Test"})
        assert response.status_code == 401

    async def test_search_case_insensitive(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test search is case insensitive"""
        customer = Customer(
            account_no="SEARCH001",
            name="Mixed Case Customer",
            email="MixedCase@Example.Com",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE
        )
        db_session.add(customer)
        await db_session.commit()

        # Search with different cases
        for search_term in ["mixed", "MIXED", "Mixed", "case", "CASE"]:
            response = await client.get(f"/api/customers/?search={search_term}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["name"] == "Mixed Case Customer"

    async def test_search_empty_results(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test search with no matching results"""
        customer = Customer(
            account_no="EMPTY001",
            name="Test Customer",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE
        )
        db_session.add(customer)
        await db_session.commit()

        response = await client.get("/api/customers/?search=nonexistent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_search_special_characters(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test search handles special characters without error (no SQL injection)."""
        customer = Customer(
            account_no="SPEC001",
            name="O'Brien & Sons",
            account_type=AccountType.RETAIL,
            status=CustomerStatus.ACTIVE,
        )
        db_session.add(customer)
        await db_session.commit()

        # Special characters must be treated as literals and never crash.
        for term in ["O'Brien", "%", "_", "&", "' OR '1'='1"]:
            response = await client.get(
                "/api/customers/", params={"search": term}, headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data and "total" in data

        # The legitimate apostrophe search still finds the record.
        response = await client.get(
            "/api/customers/", params={"search": "O'Brien"}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1