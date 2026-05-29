"""Tests for authentication endpoints"""
import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from jose import jwt as jose_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.utils.security import (
    verify_password,
    verify_access_token,
    create_access_token,
    ALLOWED_ALGORITHMS,
)


def _make_unsigned_none_token(claims: dict) -> str:
    """Craft a JWT that uses the insecure 'none' algorithm (empty signature).

    python-jose refuses to *encode* an alg=none token, so we build it by hand
    exactly as an attacker attempting a signature-bypass forgery would.
    """
    def _b64(obj: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()

    header = _b64({"alg": "none", "typ": "JWT"})
    payload = _b64(claims)
    return f"{header}.{payload}."


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
        
        response = await client.post("/api/auth/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]

    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpass",
            "new_password": "newpass456"
        }
        
        response = await client.post("/api/auth/change-password", json=password_data, headers=auth_headers)

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


class TestJWTSecurity:
    """Security tests for JWT handling: reject alg=none and enforce key management."""

    def test_jwt_security_none_algorithm_rejected_by_verify(self):
        """A token forged with the 'none' algorithm must be rejected (401)."""
        forged = _make_unsigned_none_token({
            "user_id": "admin",
            "username": "admin",
            "type": "access",
            "sub": "admin",
        })
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(forged)
        assert exc_info.value.status_code == 401

    async def test_jwt_security_none_algorithm_rejected_via_api(
        self, client: AsyncClient, test_user: User
    ):
        """A protected endpoint must reject an alg=none token with 401, not 200."""
        forged = _make_unsigned_none_token({
            "user_id": test_user.id,
            "username": test_user.username,
            "type": "access",
            "sub": test_user.id,
        })
        response = await client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {forged}"}
        )
        assert response.status_code == 401

    def test_jwt_security_wrong_signature_rejected(self):
        """A token signed with a different key must be rejected (401)."""
        now = datetime.now(timezone.utc)
        forged = jose_jwt.encode(
            {
                "user_id": "x",
                "username": "x",
                "type": "access",
                "sub": "x",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            "a-totally-different-wrong-signing-key-0123456789abcdef",
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(forged)
        assert exc_info.value.status_code == 401

    def test_jwt_security_secret_key_not_hardcoded(self):
        """The signing key must be strong and not a known weak/placeholder value."""
        weak_values = {
            "your-secret-key",
            "secret",
            "secret-key",
            "changeme",
            "change_me",
            "change_me_in_production_use_openssl_rand_base64_32",
            "test",
            "password",
        }
        assert settings.SECRET_KEY, "SECRET_KEY must be set"
        assert len(settings.SECRET_KEY) >= 32, "SECRET_KEY must be at least 32 chars"
        assert settings.SECRET_KEY.strip().lower() not in weak_values

    def test_jwt_security_none_not_in_allowed_algorithms(self):
        """'none' must never appear in the allowed-algorithms list."""
        assert "none" not in [a.lower() for a in ALLOWED_ALGORITHMS]
        assert settings.ALGORITHM.lower() != "none"

    def test_jwt_security_valid_token_roundtrip(self):
        """A properly signed token must still verify successfully."""
        token = create_access_token({"user_id": "u1", "username": "alice"})
        payload = verify_access_token(token)
        assert payload["user_id"] == "u1"
        assert payload["username"] == "alice"