"""Tests for authentication endpoints"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.security import verify_password


class TestAuthEndpoints:
    """Test authentication endpoints"""

    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"

    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate username"""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "newpass123",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email"""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "newpass123",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_register_invalid_password(self, client: AsyncClient):
        """Test registration with invalid password"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "weak",  # Too short, no digits
            "full_name": "New User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 422

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login"""
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == test_user.username

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        
        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user info"""
        response = await client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth"""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401

    async def test_update_profile(self, client: AsyncClient, auth_headers: dict):
        """Test updating user profile"""
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        
        response = await client.put("/api/auth/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

    async def test_change_password_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful password change"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newpass456"
        }
        
        response = await client.put("/api/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]

    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpass",
            "new_password": "newpass456"
        }
        
        response = await client.put("/api/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    async def test_refresh_token(self, client: AsyncClient, auth_headers: dict):
        """Test token refresh"""
        response = await client.post("/api/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_verify_token(self, client: AsyncClient, auth_headers: dict):
        """Test token verification"""
        response = await client.post("/api/auth/verify", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data

    async def test_logout(self, client: AsyncClient, auth_headers: dict):
        """Test logout endpoint"""
        response = await client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]