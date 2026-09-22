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


class TestLetterMojibakeAutoRepair:
    """v127 — letters written from a PDF with a non-standard font encoding hold
    reversibly scrambled text. The owner must not have to press anything: the
    repair runs on READ (so an old letter looks right immediately) and on WRITE
    (so it becomes permanently right the next time it is saved)."""

    GARBLED_TABLE = (
        '<table class="tblw" style="width:96%">'
        '<tr><th style="width:12%">ÒÑ</th><th>ß½½±«²¬ Ò¿³»</th><th>ß³±«²¬ (×ÎÎ)</th></tr>'
        '<tr><td>1</td><td>ßÓ×Î ØÑÍÍÛ×Ò ÓÑÌßÙØ×</td><td>4,819,650</td></tr>'
        "</table>"
    )

    async def test_an_already_garbled_letter_reads_back_correct(
            self, client: AsyncClient, admin_headers: dict, db_session):
        """Simulates a letter saved BEFORE the fix: the DB row stays as it was,
        but the API must hand the browser the repaired text."""
        import json as _json
        from app.models.letter import Letter, generate_letter_id

        lid = generate_letter_id()
        db_session.add(Letter(
            id=lid, category="general", title="صورت حساب",
            values_json=_json.dumps({
                "subject": "مشخصات املاک و صورت حساب",
                "body": "<p>گزارشِ «شعبه»</p>",
                "attTables": [{"id": "t1", "title": "جدول", "html": self.GARBLED_TABLE}],
            }, ensure_ascii=False)))
        await db_session.commit()

        vals = (await client.get(f"/api/letters/{lid}", headers=admin_headers)).json()["values"]
        html = vals["attTables"][0]["html"]
        assert ">NO<" in html and ">Account Name<" in html and ">Amount (IRR)<" in html
        assert ">AMIR HOSSEIN MOTAGHI<" in html
        # ...and the table the user built is structurally untouched
        assert 'class="tblw"' in html and "width:96%" in html and "width:12%" in html
        assert ">4,819,650<" in html            # numbers were never garbled
        assert vals["subject"] == "مشخصات املاک و صورت حساب"
        assert vals["body"] == "<p>گزارشِ «شعبه»</p>"   # Persian «quotes» untouched

    async def test_saving_a_garbled_letter_stores_it_repaired(
            self, client: AsyncClient, admin_headers: dict, db_session):
        from app.models.letter import Letter

        r = await client.post("/api/letters/", json={
            "title": "صورت حساب", "general": True,
            "values": {"body": "<p>ÒÑ</p>", "attTables": [{"id": "t1", "title": "x", "html": self.GARBLED_TABLE}]},
        }, headers=admin_headers)
        assert r.status_code == 201
        row = await db_session.get(Letter, r.json()["id"])
        assert "ÒÑ" not in (row.values_json or "")      # stored clean, not just shown clean
        assert ">Account Name<" in row.values_json

    async def test_a_clean_letter_is_stored_byte_for_byte(
            self, client: AsyncClient, admin_headers: dict, db_session):
        """The repair must be a no-op for every normal letter."""
        import json as _json
        from app.models.letter import Letter

        values = {"subject": "افتتاح حساب", "body": "<p>متنِ «عادی» — ۱۴۰۵/۰۶/۳۱</p>",
                  "attTables": [], "serial": 182}
        r = await client.post("/api/letters/", json={"title": "t", "general": True, "values": values},
                              headers=admin_headers)
        row = await db_session.get(Letter, r.json()["id"])
        assert _json.loads(row.values_json) == values
