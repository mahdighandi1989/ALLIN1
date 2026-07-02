"""Characterization tests: the startup data-merge must never clobber operator
edits or resurrect soft-deleted facilities.

_merge_facilities runs on EVERY startup (db_init) and on /api/crm/run-merge.
Before the fix it unconditionally set is_deleted=False and overwrote
facility_type/currency/name/amount from the legacy workbook JSON — so a
facility an operator deleted or corrected in the panel silently reverted on
the next deploy.
"""
from decimal import Decimal

import pytest

from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.services import data_merge


@pytest.fixture
def merge_rows(monkeypatch):
    """Route _load('facilities.json') to test-provided rows."""
    holder = {"rows": []}

    def fake_load(name):
        if name == "facilities.json":
            return holder["rows"]
        return []

    monkeypatch.setattr(data_merge, "_load", fake_load)
    return holder


async def _mk_customer(db, account_no="DM-1"):
    c = Customer(account_no=account_no, name="Merge Co")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


class TestMergeFacilities:
    async def test_deleted_facility_stays_deleted(self, db_session, merge_rows):
        c = await _mk_customer(db_session, "DM-2")
        f = Facility(
            customer_id=c.id, name="Deleted by operator",
            facility_type=FacilityType.LOAN, amount=100,
            status=FacilityStatus.ACTIVE, risk_rating="medium", is_deleted=True,
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)

        merge_rows["rows"] = [{
            "facility_id": f.id, "account_no": "DM-2",
            "facility_type": "loan", "amount_num": 999999, "currency": "USD",
        }]
        await data_merge._merge_facilities(db_session)
        await db_session.commit()
        await db_session.refresh(f)
        assert f.is_deleted is True          # NOT resurrected
        assert f.amount == 100               # NOT overwritten

    async def test_operator_edits_not_overwritten(self, db_session, merge_rows):
        c = await _mk_customer(db_session, "DM-3")
        f = Facility(
            customer_id=c.id, name="Corrected name",
            facility_type=FacilityType.LC, amount=Decimal("5000"),
            currency="USD", status=FacilityStatus.ACTIVE, risk_rating="medium",
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)

        merge_rows["rows"] = [{
            "facility_id": f.id, "account_no": "DM-3",
            "facility_type": "loan", "facility_no": "OLD NAME",
            "amount_num": 111, "currency": "AED",
        }]
        await data_merge._merge_facilities(db_session)
        await db_session.commit()
        await db_session.refresh(f)
        assert f.facility_type == FacilityType.LC
        assert f.name == "Corrected name"
        assert f.currency == "USD"
        assert f.amount == Decimal("5000")

    async def test_placeholder_still_gets_filled(self, db_session, merge_rows):
        c = await _mk_customer(db_session, "DM-4")
        f = Facility(
            customer_id=c.id, name="",
            facility_type=FacilityType.OTHER, amount=0,
            currency=None, status=FacilityStatus.ACTIVE, risk_rating="medium",
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)

        merge_rows["rows"] = [{
            "facility_id": f.id, "account_no": "DM-4",
            "facility_type": "loan", "facility_no": "FAC-77",
            "amount_num": 2500, "currency": "AED",
        }]
        touched = await data_merge._merge_facilities(db_session)
        await db_session.commit()
        await db_session.refresh(f)
        assert touched == 1
        assert f.facility_type == FacilityType.LOAN
        assert f.name == "FAC-77"
        assert f.currency == "AED"
        assert f.amount == Decimal("2500")

    async def test_new_facility_created_for_known_customer(self, db_session, merge_rows):
        await _mk_customer(db_session, "DM-5")
        merge_rows["rows"] = [{
            "facility_id": "FNEW123", "account_no": "DM-5",
            "facility_type": "overdraft", "amount_num": 700, "currency": "AED",
        }]
        touched = await data_merge._merge_facilities(db_session)
        await db_session.commit()
        assert touched == 1
        created = (
            await db_session.get(Facility, "FNEW123")
        )
        assert created is not None
        assert created.facility_type == FacilityType.OVERDRAFT
