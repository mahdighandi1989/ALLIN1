"""Tests for the full customer-listing merge (app.services.data_merge).

Covers the two waves added for the bank's core-banking export:

* ``_merge_customer_listing``          — creates a Customer per 6-digit account.
* ``_merge_customer_listing_profiles`` — creates the credit-file CustomerProfile.

Both must be idempotent and strictly non-destructive (fill empty columns only,
never overwrite real data already on a row).
"""
import json

import pytest
from sqlalchemy import func, select

from app.models.crm import CustomerProfile
from app.models.customer import AccountType, Customer, CustomerStatus
from app.services import data_merge

# A tiny, controlled listing so we can assert exact merge semantics. One brand-new
# account and one that already exists in the panel (to exercise the fill path).
_SMALL = [
    {
        "account_no": "100001",
        "name": "NEW TRADING CO",
        "account_type": "corporate",
        "branch_label": "Bur Dubai (2533)",
        "branch_code": "2533",
        "entity_type": "Company",
        "nationality": "IRAN",
        "passport_no": "P-NEW-1",
        "status_desc": "Added",
        "pep_status": "Non PEP",
        "rr_pep": "24",
        "email": "info@newco.ae",
        "mobile": "0501234567",
    },
    {
        "account_no": "200002",
        "name": "LISTING NAME (ignored if set)",
        "account_type": "retail",
        "branch_label": "Al Ain (1741)",
        "branch_code": "1741",
        "entity_type": "Individual",
        "email": "listing@x.com",
        "mobile": "0509999999",
        "nationality": "UNITED ARAB EMIRATES",
    },
]


@pytest.fixture
def small_listing(monkeypatch):
    # _iter_listing is a generator; return a FRESH iterator on each call so both
    # merge waves (and idempotency re-runs) can iterate it independently.
    monkeypatch.setattr(data_merge, "_iter_listing", lambda: iter(_SMALL))


async def _count(session, model):
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_helpers_pure():
    assert data_merge._atype({"account_type": "corporate"}) == "corporate"
    assert (
        data_merge._atype({"account_type": "PARTNERSHIP-ish"}) == "retail"
    )  # unknown -> retail
    assert data_merge._atype({}) == "retail"
    assert (
        data_merge._customer_branch({"branch_label": "Sharjah (2776)"})
        == "Sharjah (2776)"
    )
    assert data_merge._customer_branch({"branch_code": "2776"}) == "2776"

    class Obj:
        name = "Keep Me"
        branch = ""
        email = None

    obj = Obj()
    changed = data_merge._fill_empty(
        obj, {"name": "NEW", "branch": "Dubai", "email": "  ", "phone": "x"}
    )
    assert changed is True
    assert obj.name == "Keep Me"  # non-empty preserved
    assert obj.branch == "Dubai"  # empty string filled
    assert obj.email is None  # whitespace-only ignored
    assert not hasattr(obj, "phone") or getattr(obj, "phone") == "x"  # unknown attr set


async def test_customer_listing_creates_and_fills(db_session, small_listing):
    # Pre-existing account 200002 with some fields already set and some empty.
    db_session.add(
        Customer(
            account_no="200002",
            name="ORIGINAL NAME",
            email="original@x.com",
            branch=None,
            mobile=None,
        )
    )
    await db_session.commit()

    touched = await data_merge._merge_customer_listing(db_session)
    await db_session.commit()
    assert touched == 2  # one created (100001) + one filled (200002)

    # New account created with mapped branch label + account type.
    new = (
        await db_session.execute(
            select(Customer).where(Customer.account_no == "100001")
        )
    ).scalar_one()
    assert new.name == "NEW TRADING CO"
    assert new.account_type == AccountType.CORPORATE
    assert new.status == CustomerStatus.ACTIVE
    assert new.branch == "Bur Dubai (2533)"
    assert new.mobile == "0501234567"

    # Existing account: empty fields filled, real data NOT overwritten.
    ex = (
        await db_session.execute(
            select(Customer).where(Customer.account_no == "200002")
        )
    ).scalar_one()
    assert ex.name == "ORIGINAL NAME"  # preserved (listing did NOT clobber)
    assert ex.email == "original@x.com"  # preserved
    assert ex.branch == "Al Ain (1741)"  # was empty -> filled
    assert ex.mobile == "0509999999"  # was empty -> filled

    # Idempotent: a second run changes nothing and inserts nothing.
    again = await data_merge._merge_customer_listing(db_session)
    await db_session.commit()
    assert again == 0
    assert await _count(db_session, Customer) == 2


async def test_customer_listing_profiles_creates_and_fills(db_session, small_listing):
    # A legacy-style rich profile already exists for 200002 with a real passport.
    db_session.add(
        CustomerProfile(
            account_no="200002",
            customer_name=None,
            branch=None,
            passport_no="LEGACY-PASSPORT",
        )
    )
    await db_session.commit()

    touched = await data_merge._merge_customer_listing_profiles(db_session)
    await db_session.commit()
    assert touched == 2  # one created (100001) + one filled (200002)

    # New profile carries the listing's KYC + verbatim extras in data_json.
    p = (
        await db_session.execute(
            select(CustomerProfile).where(CustomerProfile.account_no == "100001")
        )
    ).scalar_one()
    assert p.branch == "2533"  # raw code stored on the profile
    assert p.passport_no == "P-NEW-1"
    assert p.passport_nationality == "IRAN"
    assert p.account_type == "Company"
    data = json.loads(p.data_json)
    assert data["pep_status"] == "Non PEP"
    assert data["source"] == "customer_listing"

    # Existing profile: real passport preserved, empty fields filled.
    ex = (
        await db_session.execute(
            select(CustomerProfile).where(CustomerProfile.account_no == "200002")
        )
    ).scalar_one()
    assert ex.passport_no == "LEGACY-PASSPORT"  # preserved
    assert ex.branch == "1741"  # was empty -> filled
    assert ex.customer_name == "LISTING NAME (ignored if set)"  # was empty -> filled

    # Idempotent.
    again = await data_merge._merge_customer_listing_profiles(db_session)
    await db_session.commit()
    assert again == 0
    assert await _count(db_session, CustomerProfile) == 2


async def test_real_listing_file_end_to_end(db_session):
    """The committed customer_listing.jsonl.gz streams, imports every 6-digit
    account exactly once, and is idempotent on a second pass."""
    records = list(data_merge._iter_listing())
    assert len(records) == 44512, "expected the distilled 6-digit account set"
    # Every account number is exactly 6 digits (the agreed rule).
    assert all(len(r["account_no"]) == 6 and r["account_no"].isdigit() for r in records)

    created = await data_merge._merge_customer_listing(db_session)
    await db_session.commit()
    assert created == 44512
    assert await _count(db_session, Customer) == 44512

    # Spot-check a known head-office (3535) account and its branch label.
    c = (
        await db_session.execute(
            select(Customer).where(Customer.account_no == "100100")
        )
    ).scalar_one()
    assert c.name == "A-DHBI CM BK"
    assert c.branch == "Head Office (3535)"

    # Profiles wave.
    created_p = await data_merge._merge_customer_listing_profiles(db_session)
    await db_session.commit()
    assert created_p == 44512
    assert await _count(db_session, CustomerProfile) == 44512

    p = (
        await db_session.execute(
            select(CustomerProfile).where(CustomerProfile.account_no == "100100")
        )
    ).scalar_one()
    assert p.branch == "3535"
    assert json.loads(p.data_json)["pep_status"] == "Non PEP"

    # Idempotent: re-running both waves inserts nothing.
    assert await data_merge._merge_customer_listing(db_session) == 0
    assert await data_merge._merge_customer_listing_profiles(db_session) == 0
    await db_session.commit()
    assert await _count(db_session, Customer) == 44512
    assert await _count(db_session, CustomerProfile) == 44512
