"""Saved letters: under an account (auto-creating the profile) or general."""
from httpx import AsyncClient
from sqlalchemy import select

from app.models.customer import Customer


class TestLetters:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/letters/")).status_code == 401

    async def test_save_under_account_autocreates_profile(self, client: AsyncClient, admin_headers: dict, db_session):
        # account LET-1 does NOT exist yet
        r = await client.post("/api/letters/", json={
            "account_no": "LET-1", "title": "نامهٔ تست", "subject": "افتتاح",
            "recipient_dept": "اداره کل خارجه", "recipient_manager": "آقای الف",
            "values": {"body": "متن", "subject": "افتتاح"}, "layout": {"body": {"y": 10}},
        }, headers=admin_headers)
        assert r.status_code == 201
        lid = r.json()["id"]
        # the customer/profile was auto-created (like collateral/facilities)
        cust = (await db_session.execute(select(Customer).where(Customer.account_no == "LET-1"))).scalar_one_or_none()
        assert cust is not None
        # listed under the account, and full fetch returns the stored values + layout
        lst = await client.get("/api/letters/?account_no=LET-1", headers=admin_headers)
        assert lst.status_code == 200 and any(x["id"] == lid for x in lst.json())
        full = await client.get(f"/api/letters/{lid}", headers=admin_headers)
        assert full.json()["values"]["body"] == "متن" and full.json()["layout"]["body"]["y"] == 10

    async def test_general_letter_bucket(self, client: AsyncClient, admin_headers: dict):
        r = await client.post("/api/letters/", json={"general": True, "title": "بخشنامهٔ عمومی", "values": {"body": "x"}}, headers=admin_headers)
        assert r.status_code == 201 and r.json()["category"] == "general"
        g = await client.get("/api/letters/?general=true", headers=admin_headers)
        assert any(x["id"] == r.json()["id"] for x in g.json())
        # general letters are NOT tied to an account
        assert r.json()["account_no"] in (None, "")

    async def test_update_and_delete(self, client: AsyncClient, admin_headers: dict):
        r = await client.post("/api/letters/", json={"account_no": "LET-2", "title": "اول", "values": {"body": "a"}}, headers=admin_headers)
        lid = r.json()["id"]
        u = await client.patch(f"/api/letters/{lid}", json={"account_no": "LET-2", "title": "دوم", "values": {"body": "b"}}, headers=admin_headers)
        assert u.status_code == 200 and u.json()["title"] == "دوم" and u.json()["values"]["body"] == "b"
        assert (await client.delete(f"/api/letters/{lid}", headers=admin_headers)).status_code == 204
        lst = await client.get("/api/letters/?account_no=LET-2", headers=admin_headers)
        assert not any(x["id"] == lid for x in lst.json())

    async def test_letter_is_audited_under_account(self, client: AsyncClient, admin_headers: dict):
        await client.post("/api/letters/", json={"account_no": "LET-3", "title": "ث", "values": {}}, headers=admin_headers)
        a = await client.get("/api/audit/?account_no=LET-3", headers=admin_headers)
        assert any(e["entity_type"] == "letter" for e in a.json()["items"])
