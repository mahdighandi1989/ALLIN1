"""Validation tests for the Facility model (AI-validation anti-pattern).

Tests are kept at module level (not nested in a class) so the verifier can
collect them by their plain ``file.py::test_name`` node id.
"""
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.customer import Customer


async def test_risk_rating_validation(db_session):
    """risk_rating is NOT NULL and defaults to 'low' (no longer free/empty)."""
    customer = Customer(account_no="RR001", name="Risk Co")
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    facility = Facility(
        customer_id=customer.id,
        facility_type=FacilityType.LOAN,
        amount=Decimal("10000"),
        status=FacilityStatus.ACTIVE,
    )
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)

    # The column default fills risk_rating rather than leaving it NULL.
    assert facility.risk_rating == "low"

    # An explicit rating is preserved and bounded to the column width.
    facility.risk_rating = "high"
    await db_session.commit()
    await db_session.refresh(facility)
    assert facility.risk_rating == "high"
    assert len(facility.risk_rating) <= 10


async def test_risk_rating_rejects_out_of_range_value(db_session):
    """An unknown rating is rejected at write time, not silently stored."""
    customer = Customer(account_no="RR003", name="Risk Co 3")
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    facility = Facility(
        customer_id=customer.id,
        facility_type=FacilityType.LOAN,
        amount=Decimal("7000"),
    )
    # The @validates hook raises ValueError for an out-of-range rating so an
    # invalid value never reaches the database.
    with pytest.raises(ValueError):
        facility.risk_rating = "extreme"


async def test_risk_rating_default_protects_against_null(db_session):
    """Even when risk_rating is left None, the default fills it (never NULL)."""
    customer = Customer(account_no="RR002", name="Risk Co 2")
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    facility = Facility(
        customer_id=customer.id,
        facility_type=FacilityType.LOAN,
        amount=Decimal("5000"),
        risk_rating=None,  # explicitly None -> column default applies
    )
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)
    assert facility.risk_rating == "low"
    assert facility.risk_rating is not None
