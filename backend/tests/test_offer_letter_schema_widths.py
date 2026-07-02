"""Characterization tests for offer-letter column widths.

SQLite (the test DB) does not enforce VARCHAR length or NUMERIC precision, so
these constraints can only be locked by asserting on the model metadata
itself. They guard two production-only failures:

- ``facility_id`` was String(8) while every real facility id is 9+ chars
  ("F" + 8 hex, column String(33)) → Postgres rejected EVERY attempt to link
  an offer letter to a facility with "value too long".
- rate fields were Numeric(5,4) (max 9.9999) while the API accepts up to 100
  (percent) → any offer at 10% or more overflowed with "numeric field
  overflow".
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.offer_letter import OfferLetter, OfferAttachment, OfferCalculation


def test_facility_fk_width_matches_facilities_pk():
    fk_len = OfferLetter.__table__.c.facility_id.type.length
    pk_len = Facility.__table__.c.id.type.length
    assert fk_len >= pk_len, (
        f"offer_letters.facility_id ({fk_len}) narrower than facilities.id ({pk_len})"
    )


def test_rate_columns_allow_percent_rates_up_to_100():
    cols = ["interest_rate", "profit_rate", "processing_fee_percentage",
            "commitment_fee", "early_settlement_fee"]
    for name in cols:
        t = OfferLetter.__table__.c[name].type
        integer_digits = t.precision - t.scale
        assert integer_digits >= 3, (
            f"offer_letters.{name} numeric({t.precision},{t.scale}) cannot store 100.0"
        )


def test_child_pk_columns_hold_full_uuids():
    for table in (OfferAttachment.__table__, OfferCalculation.__table__):
        assert table.c.id.type.length >= 36
        assert table.c.offer_letter_id.type.length >= 36
    assert OfferLetter.__table__.c.id.type.length >= 36


class TestOfferWithFacilityLink:
    async def test_create_offer_linked_to_real_facility_at_double_digit_rate(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        c = Customer(account_no="OLW-1", name="Width Test Co")
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)
        f = Facility(
            customer_id=c.id, name="Width facility",
            facility_type=FacilityType.LOAN, amount=500000,
            status=FacilityStatus.ACTIVE, risk_rating="medium",
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)
        assert len(f.id) > 8  # the premise of the bug

        r = await client.post(
            "/api/offer-letters/",
            json={
                "customer_id": c.id, "facility_id": f.id,
                "expiry_date": "2027-12-31",
                "principal_amount": 500000, "interest_rate": 12.5,
                "tenor_months": 12, "currency": "AED", "repayment_type": "monthly",
            },
            headers=auth_headers,
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["facility_id"] == f.id
        assert Decimal(str(body["interest_rate"])) == Decimal("12.5")
