"""Tests for the (not-yet-wired) offer_letter models.

These confirm the module is importable and self-consistent after the broken
Customer/Facility back-references were removed — i.e. importing it no longer
risks breaking SQLAlchemy mapper configuration.
"""
from datetime import date
from decimal import Decimal

from app.models.offer_letter import (
    OfferLetter,
    OfferAttachment,
    OfferCalculation,
    OfferStatus,
    CollateralType,
    RepaymentType,
    generate_offer_id,
)


def test_generate_offer_id_format():
    oid = generate_offer_id()
    assert oid.startswith("OL")
    assert len(oid) == 10  # "OL" + 8 chars
    assert generate_offer_id() != generate_offer_id()


def test_offer_status_enum_values():
    assert OfferStatus.DRAFT == "draft"
    assert OfferStatus.APPROVED == "approved"
    assert OfferStatus.SENT == "sent"
    assert CollateralType.PROPERTY == "property"
    assert RepaymentType.MONTHLY == "monthly"


def test_offer_letter_construction_and_repr():
    offer = OfferLetter(
        customer_id="C12345678",
        facility_id="F1234567",
        offer_date=date(2024, 1, 1),
        expiry_date=date(2024, 6, 30),
        principal_amount=Decimal("100000.00"),
        interest_rate=Decimal("5.5"),
        tenor_months=24,
        status=OfferStatus.DRAFT,
    )
    assert offer.customer_id == "C12345678"
    assert offer.principal_amount == Decimal("100000.00")
    r = repr(offer)
    assert "OfferLetter" in r
    assert "C12345678" in r
    assert "draft" in r


def test_offer_attachment_and_calculation_construction():
    att = OfferAttachment(
        offer_letter_id="OL12345678",
        filename="offer.pdf",
        original_filename="Offer Letter.pdf",
        file_path="/tmp/offer.pdf",
        file_size=1024,
        mime_type="application/pdf",
    )
    assert "OfferAttachment" in repr(att)
    assert att.filename == "offer.pdf"

    calc = OfferCalculation(
        offer_letter_id="OL12345678",
        installment_number=1,
        payment_date=date(2024, 2, 1),
        opening_balance=Decimal("100000.00"),
        principal_payment=Decimal("4000.00"),
        interest_payment=Decimal("450.00"),
        total_payment=Decimal("4450.00"),
        closing_balance=Decimal("96000.00"),
    )
    assert "OfferCalculation" in repr(calc)
    assert calc.installment_number == 1


def test_offer_letter_registered_in_active_models():
    """The offer-letter models are now wired into app.models (feature enabled)."""
    import app.models as models

    assert hasattr(models, "OfferLetter")
    assert hasattr(models, "OfferCalculation")
    assert "OfferLetter" in models.__all__
