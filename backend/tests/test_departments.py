"""Departments address book: fuzzy de-dup + manager rotation/history."""
from httpx import AsyncClient


class TestDepartments:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/departments/")).status_code == 401

    async def test_resolve_creates_then_dedups_fuzzily(self, client: AsyncClient, admin_headers: dict):
        a = await client.post("/api/departments/resolve", json={"name": "اداره کل خارجه", "manager": "آقای الف", "manager_title": "رئیس محترم"}, headers=admin_headers)
        assert a.status_code == 200
        did = a.json()["id"]
        assert a.json()["current_manager"] == "آقای الف"
        # a near-identical spelling (Arabic teh-marbuta + extra space) must MATCH, not duplicate
        b = await client.post("/api/departments/resolve", json={"name": "اداره کل  خارجة"}, headers=admin_headers)
        assert b.status_code == 200 and b.json()["id"] == did
        # a clearly different name creates a new department
        c = await client.post("/api/departments/resolve", json={"name": "اداره حقوقی و وصول"}, headers=admin_headers)
        assert c.json()["id"] != did
        lst = await client.get("/api/departments/", headers=admin_headers)
        assert len({d["id"] for d in lst.json()}) == 2

    async def test_manager_rotation_keeps_ordered_history(self, client: AsyncClient, admin_headers: dict):
        base = {"name": "اداره فناوری"}
        await client.post("/api/departments/resolve", json={**base, "manager": "مدیر اول"}, headers=admin_headers)
        await client.post("/api/departments/resolve", json={**base, "manager": "مدیر دوم"}, headers=admin_headers)
        r = await client.post("/api/departments/resolve", json={**base, "manager": "مدیر سوم"}, headers=admin_headers)
        body = r.json()
        assert body["current_manager"] == "مدیر سوم"
        prev = [p["name"] for p in (body["previous_managers"] or [])]
        assert prev == ["مدیر اول", "مدیر دوم"]   # oldest → most-recent-previous

    async def test_search(self, client: AsyncClient, admin_headers: dict):
        await client.post("/api/departments/resolve", json={"name": "اداره بازرسی", "manager": "بازرس کل"}, headers=admin_headers)
        r = await client.get("/api/departments/?q=بازرس", headers=admin_headers)
        assert r.status_code == 200 and any("بازرسی" in d["name"] for d in r.json())

    async def test_changes_are_audited(self, client: AsyncClient, admin_headers: dict):
        await client.post("/api/departments/resolve", json={"name": "اداره آمار"}, headers=admin_headers)
        a = await client.get("/api/audit/?entity_type=department", headers=admin_headers)
        assert any(e["entity_type"] == "department" for e in a.json()["items"])
