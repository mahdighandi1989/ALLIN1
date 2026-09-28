"""v139 — the account-type review endpoint.

It answers the owner's question — «how many of my records have the wrong type?»
— and lets a human fix the ones they name. The binding rule is that it NEVER
changes a record on its own: a wrong flip changes which form opens, which KYC
fields are required and how completeness is scored.
"""
import pytest

from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.crm import CustomerProfile
from app.models.profile_entities import Partner


async def _seed(db):
    # a company filed as an individual — the bug the owner reported
    db.add(Customer(account_no="900001", name="FUTURE DEAL GENERAL TRADING LLC",
                    account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE))
    # a company nobody ever classified, with a trade licence on file
    db.add(Customer(account_no="900002", name="Abu Amir Furnishing Branch",
                    account_type=AccountType.UNKNOWN, status=CustomerStatus.ACTIVE))
    db.add(CustomerProfile(account_no="900002", business_type="Corporate"))
    # a genuine individual, correctly filed
    db.add(Customer(account_no="900003", name="Mr. Ali Hassan",
                    account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE))
    db.add(CustomerProfile(account_no="900003", passport_no="A1234567"))
    # no evidence at all — must be asked about, never guessed
    db.add(Customer(account_no="900004", name="Ahmad",
                    account_type=AccountType.UNKNOWN, status=CustomerStatus.ACTIVE))
    await db.commit()


class TestReview:
    async def test_it_finds_a_company_filed_as_an_individual(self, client, auth_headers, db_session):
        await _seed(db_session)
        r = await client.get("/api/crm/account-type-review", headers=auth_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        accs = {c["account_no"] for c in d["conflicts"]}
        assert "900001" in accs
        item = next(c for c in d["conflicts"] if c["account_no"] == "900001")
        assert item["stored"] == "retail" and item["guess"] == "corporate"
        assert item["reasons"], "a finding must carry the evidence that produced it"

    async def test_undecided_is_reported_separately_from_wrong(self, client, auth_headers, db_session):
        """«nobody decided» and «the decision is wrong» need different fixes, so
        mixing the two counts would hide the real number."""
        await _seed(db_session)
        d = (await client.get("/api/crm/account-type-review", headers=auth_headers)).json()
        assert {u["account_no"] for u in d["undecided"]} >= {"900002", "900004"}
        assert "900002" not in {c["account_no"] for c in d["conflicts"]}
        assert d["summary"]["conflicts"] == 1

    async def test_it_says_which_undecided_records_the_evidence_can_already_settle(
            self, client, auth_headers, db_session):
        await _seed(db_session)
        d = (await client.get("/api/crm/account-type-review", headers=auth_headers)).json()
        # 900002's business type says corporate; 900004 has nothing
        assert d["summary"]["undecided_with_evidence"] == 1
        settled = next(u for u in d["undecided"] if u["account_no"] == "900002")
        assert settled["guess"] == "corporate" and settled["confidence"] in ("high", "medium")
        blind = next(u for u in d["undecided"] if u["account_no"] == "900004")
        assert blind["guess"] == "unknown" and blind["confidence"] == "none"

    async def test_a_correctly_filed_individual_is_not_a_finding(self, client, auth_headers, db_session):
        await _seed(db_session)
        d = (await client.get("/api/crm/account-type-review", headers=auth_headers)).json()
        flagged = {c["account_no"] for c in d["conflicts"]} | {u["account_no"] for u in d["undecided"]}
        assert "900003" not in flagged

    async def test_reading_the_review_changes_nothing(self, client, auth_headers, db_session):
        await _seed(db_session)
        await client.get("/api/crm/account-type-review", headers=auth_headers)
        from sqlalchemy import select
        t = (await db_session.execute(
            select(Customer.account_type).where(Customer.account_no == "900001"))).scalar_one()
        assert str(getattr(t, "value", t)) == "retail", "the review must be read-only"


class TestApply:
    async def test_it_changes_only_the_accounts_named(self, client, auth_headers, db_session):
        await _seed(db_session)
        r = await client.post("/api/crm/account-type-review/apply", headers=auth_headers,
                              json={"accounts": ["900001"], "account_type": "corporate"})
        assert r.status_code == 200, r.text
        assert r.json()["count"] == 1
        from sqlalchemy import select
        got = {a: str(getattr(t, "value", t)) for a, t in (await db_session.execute(
            select(Customer.account_no, Customer.account_type))).all()}
        assert got["900001"] == "corporate"
        assert got["900003"] == "retail", "an account not named must be untouched"
        assert got["900002"] == "unknown"

    async def test_it_reports_what_it_changed_and_from_what(self, client, auth_headers, db_session):
        await _seed(db_session)
        r = await client.post("/api/crm/account-type-review/apply", headers=auth_headers,
                              json={"accounts": ["900001"], "account_type": "corporate"})
        assert r.json()["changed"] == [{"account_no": "900001", "from": "retail", "to": "corporate"}]

    async def test_an_invalid_type_is_refused(self, client, auth_headers, db_session):
        await _seed(db_session)
        r = await client.post("/api/crm/account-type-review/apply", headers=auth_headers,
                              json={"accounts": ["900001"], "account_type": "banana"})
        assert r.status_code == 422

    async def test_there_is_no_fix_everything_switch(self, client, auth_headers, db_session):
        """An empty account list must be refused, so nothing can sweep the book
        on a heuristic."""
        await _seed(db_session)
        r = await client.post("/api/crm/account-type-review/apply", headers=auth_headers,
                              json={"accounts": [], "account_type": "corporate"})
        assert r.status_code == 422

    async def test_it_requires_a_logged_in_user(self, client, db_session):
        await _seed(db_session)
        r = await client.post("/api/crm/account-type-review/apply",
                              json={"accounts": ["900001"], "account_type": "corporate"})
        assert r.status_code in (401, 403)
