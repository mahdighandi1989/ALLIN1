"""v130 — honest completeness + the whole-book data-quality sweep.

The owner's report: "the database is full of junk and gaps, and I only find out
when I fill the Summary form by hand." The cause was that completeness scored
**13 items** (10 profile fields + 3 existence checks), so a record could read
100% while most of what the Summary form needs was empty. These tests pin the
new contract: the score covers what the forms actually read, it is account-type
aware, and the sweep answers "where is my data worst" in one call.
"""
import pytest
from httpx import AsyncClient

from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.crm import CustomerProfile
from app.services import completeness as comp


class _Prof:
    """A stand-in profile object — build_report only reads attributes."""
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
    def __getattr__(self, _):
        return None


def test_scores_far_more_than_the_old_thirteen_items():
    r = comp.build_report("1", "corporate", _Prof(), {})
    assert r["total"] >= 35, "the old scope (13) was the bug — it must be much wider now"
    assert r["percent"] == 0 and r["filled"] == 0


def test_account_type_decides_which_fields_are_required():
    corp = {a for _, a, _ in comp.field_specs_for("corporate")}
    retail = {a for _, a, _ in comp.field_specs_for("retail")}
    # a retail customer can never hold a trade licence or a tenancy contract
    for only_corp in ("trade_license_no", "trade_license_expiry", "tenancy_no", "business_type"):
        assert only_corp in corp and only_corp not in retail
    # ...and a salary is asked of retail, not of a company
    assert "monthly_salary" in retail and "monthly_salary" not in corp
    # the shared identity/KYC core is asked of both
    for shared in ("passport_no", "passport_expiry", "emirates_id_no", "passport_nationality", "rating"):
        assert shared in corp and shared in retail


def test_every_spec_attribute_is_a_real_profile_column():
    """A spec entry naming a field that is not a column would read as permanently
    missing and quietly depress every score — the model's friendly alias
    ("nationality") is NOT the column name ("passport_nationality")."""
    from app.models.crm import CustomerProfile
    cols = {c.name for c in CustomerProfile.__table__.columns}
    for section, attr, label in comp.field_specs_for("corporate") + comp.field_specs_for("retail"):
        assert attr in cols, f"{attr} ({label}) is not a CustomerProfile column"
        assert label.strip(), f"{attr} has no label"


def test_officer_remarks_are_not_counted_as_a_data_gap():
    """`*_remarks` hold the OFFICER'S notes; a document never states them, so an
    empty one is not missing data and must not drag the score down."""
    attrs = {a for _, a, _ in comp.field_specs_for("corporate")}
    for r in ("trade_license_remarks", "passport_remarks", "emirates_id_remarks"):
        assert r not in attrs


def test_a_full_record_reaches_one_hundred_percent():
    prof = _Prof(**{a: "x" for _, a, _ in comp.field_specs_for("corporate")})
    counts = {"facilities": 1, "guarantors": 1, "securities": 0,
              "properties": 1, "deposits": 0, "partners": 2}
    r = comp.build_report("1", "corporate", prof, counts)
    assert r["percent"] == 100 and r["missing"] == []


def test_sections_add_up_and_carry_their_own_missing_list():
    r = comp.build_report("1", "corporate", _Prof(rating="A"), {"facilities": 1})
    assert sum(s["total"] for s in r["sections"]) == r["total"]
    assert sum(s["filled"] for s in r["sections"]) == r["filled"]
    keys = [s["key"] for s in r["sections"]]
    assert keys == ["identity", "kyc", "credit", "records"]
    credit = next(s for s in r["sections"] if s["key"] == "credit")
    assert "rating" not in [m["field"] for m in credit["missing"]]   # it is filled
    records = next(s for s in r["sections"] if s["key"] == "records")
    assert "facilities" not in [m["field"] for m in records["missing"]]


def test_whitespace_only_value_counts_as_missing():
    r = comp.build_report("1", "retail", _Prof(passport_no="   "), {})
    assert "شمارهٔ پاسپورت" in r["missing"]


def test_unknown_account_type_is_scored_strictly_as_corporate():
    """An unknown type must not be let off the wider corporate requirements."""
    assert comp.normalize_account_type(None) == "corporate"
    assert comp.normalize_account_type("") == "corporate"
    assert comp.normalize_account_type("RETAIL") == "retail"


class TestDataQualitySweep:
    async def _seed(self, db_session):
        db_session.add(Customer(account_no="900001", name="Empty Corp",
                                account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE))
        db_session.add(Customer(account_no="900002", name="Better Corp", branch="Main",
                                account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE))
        db_session.add(CustomerProfile(account_no="900002", customer_name="Better Corp",
                                       rating="A", passport_nationality="IR", passport_no="P9",
                                       trade_license_no="TL9", business_type="Trading"))
        await db_session.commit()

    async def test_sweep_ranks_the_worst_record_first(self, client: AsyncClient, auth_headers, db_session):
        await self._seed(db_session)
        r = await client.get("/api/crm/data-quality", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        rows = {c["account_no"]: c for c in body["customers"]}
        assert rows["900001"]["percent"] < rows["900002"]["percent"]
        order = [c["account_no"] for c in body["customers"]]
        assert order.index("900001") < order.index("900002"), "worst must sort first"

    async def test_sweep_reports_the_most_common_gap_across_the_book(
            self, client: AsyncClient, auth_headers, db_session):
        await self._seed(db_session)
        body = (await client.get("/api/crm/data-quality", headers=auth_headers)).json()
        gaps = {g["field"]: g for g in body["common_gaps"]}
        # neither seeded customer has a visa number, so it is missing for both
        assert gaps["visa_no"]["count"] >= 2
        assert gaps["visa_no"]["label"]
        # ...while the field only one of them lacks is counted once
        assert gaps["trade_license_no"]["count"] >= 1
        # counts are ordered worst-first
        counts = [g["count"] for g in body["common_gaps"]]
        assert counts == sorted(counts, reverse=True)

    async def test_sweep_carries_totals_and_section_averages(
            self, client: AsyncClient, auth_headers, db_session):
        await self._seed(db_session)
        body = (await client.get("/api/crm/data-quality", headers=auth_headers)).json()
        assert body["total_customers"] == len(body["customers"]) >= 2
        assert 0 <= body["average_percent"] <= 100
        assert [s["key"] for s in body["sections"]] == ["identity", "kyc", "credit", "records"]
        for s in body["sections"]:
            assert s["total"] > 0 and 0 <= s["percent"] <= 100

    async def test_sweep_is_empty_safe(self, client: AsyncClient, auth_headers):
        body = (await client.get("/api/crm/data-quality", headers=auth_headers)).json()
        assert body["total_customers"] == len(body["customers"])
        assert isinstance(body["common_gaps"], list)

    async def test_sweep_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/crm/data-quality")).status_code == 401
