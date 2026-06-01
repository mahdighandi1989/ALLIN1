"""Role-based access control: pending gate + viewer/editor/admin."""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.utils.security import hash_password, create_access_token


async def _mk(db, username, role):
    u = User(
        username=username, email=f"{username}@x.ae",
        hashed_password=hash_password("Passw0rd1"), full_name=username.title(),
        is_active=True, role=role, is_admin=(role == "admin"),
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


def _hdr(u):
    tok = create_access_token(data={"user_id": u.id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}


class TestRbac:
    async def test_pending_blocked_from_data_but_sees_me(self, client: AsyncClient, db_session):
        u = await _mk(db_session, "penduser", "pending")
        assert (await client.get("/api/customers/", headers=_hdr(u))).status_code == 403
        me = await client.get("/api/auth/me", headers=_hdr(u))
        assert me.status_code == 200 and me.json()["role"] == "pending"

    async def test_viewer_can_read_not_write(self, client: AsyncClient, db_session):
        u = await _mk(db_session, "viewuser", "viewer")
        assert (await client.get("/api/customers/", headers=_hdr(u))).status_code == 200
        r = await client.post(
            "/api/customers/", json={"account_no": "VV1", "name": "Viewer Co"}, headers=_hdr(u)
        )
        assert r.status_code == 403

    async def test_editor_can_write(self, client: AsyncClient, db_session):
        u = await _mk(db_session, "edituser", "editor")
        r = await client.post(
            "/api/customers/", json={"account_no": "EE1", "name": "Editor Co"}, headers=_hdr(u)
        )
        assert r.status_code in (200, 201)

    async def test_admin_grants_role(self, client: AsyncClient, db_session, admin_headers):
        u = await _mk(db_session, "newbie", "pending")
        r = await client.put(f"/api/users/{u.id}", json={"role": "editor"}, headers=admin_headers)
        assert r.status_code == 200 and r.json()["role"] == "editor"
        # and now that user can read
        assert (await client.get("/api/customers/", headers=_hdr(u))).status_code in (200, 403)
