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

    async def test_login_derives_redirect_uri_when_unset(self, client: AsyncClient, monkeypatch):
        # With only client id + secret (no explicit GOOGLE_REDIRECT_URI) Google
        # Sign-In still works: the callback URI is derived from the request and
        # encoded into the consent URL.
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "")
        r = await client.get("/api/auth/google/login", follow_redirects=False)
        assert r.status_code in (302, 307)
        loc = r.headers["location"]
        assert "accounts.google.com" in loc
        # The derived callback path is present (host-agnostic assertion).
        assert "%2Fapi%2Fauth%2Fgoogle%2Fcallback" in loc

    async def test_login_honors_forwarded_proto_for_redirect_uri(self, client: AsyncClient, monkeypatch):
        # Behind Render's TLS proxy uvicorn sees http; X-Forwarded-Proto must be
        # honoured so the derived redirect URI is the public https URL.
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "")
        r = await client.get(
            "/api/auth/google/login",
            headers={"x-forwarded-proto": "https", "x-forwarded-host": "bank.example.com"},
            follow_redirects=False,
        )
        loc = r.headers["location"]
        # https://bank.example.com/api/auth/google/callback (url-encoded)
        assert "https%3A%2F%2Fbank.example.com%2Fapi%2Fauth%2Fgoogle%2Fcallback" in loc

    async def test_login_url_has_no_incremental_scopes_by_default(self, client: AsyncClient, monkeypatch):
        # v115 — include_granted_scopes=true let Google merge unrelated grants
        # (YouTube, from another tool on the same client_id) into our request;
        # drive.file + YouTube cannot be requested together ⇒ login blocked with
        # Error 400. Default OFF; the old behavior stays behind the flag.
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "https://app/api/auth/google/callback")
        r = await client.get("/api/auth/google/login", follow_redirects=False)
        loc = r.headers["location"]
        assert "include_granted_scopes" not in loc
        # the scopes we DO need are all still requested, with offline consent
        assert "drive.file" in loc and "access_type=offline" in loc and "prompt=consent" in loc

        monkeypatch.setattr(settings, "GOOGLE_INCLUDE_GRANTED_SCOPES", True)
        r2 = await client.get("/api/auth/google/login", follow_redirects=False)
        assert "include_granted_scopes=true" in r2.headers["location"]

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
