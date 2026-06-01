"""Google sign-in: redirect behavior + user upsert/role assignment."""
import pytest
from httpx import AsyncClient

from app.config import settings
from app.routers.google_auth import upsert_google_user


class TestGoogleLogin:
    async def test_login_redirects_to_google_when_configured(self, client: AsyncClient, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "https://app/api/auth/google/callback")
        r = await client.get("/api/auth/google/login", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert "accounts.google.com" in r.headers["location"]

    async def test_login_errors_when_not_configured(self, client: AsyncClient, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
        r = await client.get("/api/auth/google/login", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert "google_not_configured" in r.headers["location"]

    async def test_callback_state_mismatch_redirects_to_error(self, client: AsyncClient):
        r = await client.get(
            "/api/auth/google/callback?code=x&state=abc", follow_redirects=False
        )
        assert r.status_code in (302, 307)
        assert "state_mismatch" in r.headers["location"]


class TestGoogleUpsert:
    async def test_normal_email_is_pending(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "ADMIN_EMAILS", "")
        u = await upsert_google_user(
            db_session, {"sub": "g1", "email": "joe@gmail.com", "name": "Joe"}, {"refresh_token": "rt"}
        )
        assert u.role == "pending"
        assert u.auth_provider == "google" and u.google_sub == "g1"
        assert u.google_refresh_token == "rt"

    async def test_admin_email_becomes_admin(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss@gmail.com")
        u = await upsert_google_user(
            db_session, {"sub": "g2", "email": "boss@gmail.com", "name": "Boss"}, {}
        )
        assert u.role == "admin" and u.is_admin is True

    async def test_second_login_updates_same_user(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "ADMIN_EMAILS", "")
        u1 = await upsert_google_user(db_session, {"sub": "g3", "email": "z@gmail.com", "name": "Z"}, {})
        u2 = await upsert_google_user(db_session, {"sub": "g3", "email": "z@gmail.com", "name": "Z"}, {})
        assert u1.id == u2.id  # matched by google_sub, not duplicated
