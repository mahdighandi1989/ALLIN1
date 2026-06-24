"""Tests for the staff directory (CRUD, search, editable Persian name, seed)."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, func

from app.models.staff import StaffMember


class TestStaffDirectory:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/staff/")).status_code == 401

    async def test_crud_search_and_persian_name(self, client: AsyncClient, admin_headers: dict):
        # create with a Persian equivalent
        r = await client.post("/api/staff/", json={
            "name": "Ali Reza", "name_fa": "علی‌رضا",
            "department": "Credit Facility Dept.", "ext": "123",
            "email": "ali.reza@bsi.co.ae",
        }, headers=admin_headers)
        assert r.status_code == 201
        sid = r.json()["id"]
        assert r.json()["name_fa"] == "علی‌رضا"

        # appears in the list
        lst = await client.get("/api/staff/", headers=admin_headers)
        assert lst.status_code == 200 and any(s["id"] == sid for s in lst.json()["items"])

        # searchable by Persian name and by extension
        assert any(s["id"] == sid for s in (await client.get("/api/staff/?q=علی‌رضا", headers=admin_headers)).json()["items"])
        assert any(s["id"] == sid for s in (await client.get("/api/staff/?q=123", headers=admin_headers)).json()["items"])

        # editable: person moved department + fixed the Persian spelling
        u = await client.patch(f"/api/staff/{sid}", json={"department": "Finance Dept.", "name_fa": "علیرضا"}, headers=admin_headers)
        assert u.status_code == 200 and u.json()["department"] == "Finance Dept." and u.json()["name_fa"] == "علیرضا"

        # departments list reflects the move
        assert "Finance Dept." in (await client.get("/api/staff/departments", headers=admin_headers)).json()

        # soft-delete removes it from the list
        assert (await client.delete(f"/api/staff/{sid}", headers=admin_headers)).status_code == 204
        assert not any(s["id"] == sid for s in (await client.get("/api/staff/", headers=admin_headers)).json()["items"])

    async def test_staff_changes_are_audited(self, client: AsyncClient, admin_headers: dict):
        r = await client.post("/api/staff/", json={"name": "Logged Staff"}, headers=admin_headers)
        assert r.status_code == 201
        a = await client.get("/api/audit/?entity_type=staff", headers=admin_headers)
        assert a.status_code == 200
        assert any(e["action"] == "create" and e["entity_type"] == "staff" for e in a.json()["items"])

    async def test_seed_is_idempotent(self, db_session):
        from app.services.staff_seed import seed_staff
        n = await seed_staff(db_session)
        assert n > 100  # the bundled Persian-Gulf directory
        cnt = (await db_session.execute(select(func.count()).select_from(StaffMember))).scalar()
        assert cnt == n
        # running again does nothing (never clobbers later edits)
        assert await seed_staff(db_session) == 0
