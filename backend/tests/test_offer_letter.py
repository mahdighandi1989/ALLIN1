"""Tests for the offer_letter models.

These confirm the module is importable and self-consistent after the broken
Customer/Facility back-references were removed — i.e. importing it no longer
risks breaking SQLAlchemy mapper configuration — and that the model persists and
round-trips through a real database session.

Sync note — diff of ``app/models/offer_letter.py`` reviewed for impact on this
test (AC: "diff offer_letter.py بررسی شد و تأثیر بر test_offer_letter.py مستند شد"):

The current ``OfferLetter`` contract these tests are aligned with:
  * primary key ``id`` (``"OL" + 8 hex chars``, via ``generate_offer_id``),
  * ``customer_id`` (required) / ``facility_id`` (optional) FK columns,
  * ``status`` / ``repayment_type`` / ``collateral_type`` stored through
    ``TolerantEnum`` as the enum *value* ("draft", "monthly", ...), not the
    member NAME, so ``== "draft"`` filters/asserts hold,
  * ``Numeric(18, 2)`` money columns that round-trip as ``Decimal``,
  * the Customer/Facility back-references are intentionally **absent** (only the
    FK columns link them), while ``attachments`` and ``calculations`` are real
    relationships with ``cascade="all, delete-orphan"``.
No column referenced by these tests was renamed/removed in the model; the
integration test below additionally pins the persisted-value contract so a
future model change (enum storage, nullability, relationship cascade) is caught
here instead of silently regressing downstream consumers.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
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


def test_offer_letter_persists_and_roundtrips_integration():
    """Integration: persist an OfferLetter (+ calculation + attachment) and read it back.

    Covers both ``app/models/offer_letter.py`` and this test together against a
    real SQLite database. It asserts the persisted-value contract the rest of
    the app relies on:

    * the python-side default fills ``id`` with an ``OL...`` primary key,
    * enum columns are stored/read as their string *value* ("draft", "monthly",
      "property") via ``TolerantEnum``,
    * ``Numeric`` money columns round-trip exactly as ``Decimal``,
    * the ``calculations`` / ``attachments`` relationships load back, and the
      ``cascade="all, delete-orphan"`` deletes children with the parent.
    """
    # Ensure every model/mapper is registered before create_all so all tables
    # (and the relationship targets) exist.
    import app.models  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            offer = OfferLetter(
                customer_id="C12345678",
                facility_id="F1234567",
                offer_date=date(2024, 1, 1),
                expiry_date=date(2024, 6, 30),
                principal_amount=Decimal("100000.00"),
                interest_rate=Decimal("5.5000"),
                tenor_months=24,
                status=OfferStatus.DRAFT,
                repayment_type=RepaymentType.MONTHLY,
                collateral_type=CollateralType.PROPERTY,
                collateral_value=Decimal("250000.00"),
            )
            offer.attachments.append(
                OfferAttachment(
                    filename="offer.pdf",
                    original_filename="Offer Letter.pdf",
                    file_path="/tmp/offer.pdf",
                    file_size=2048,
                    mime_type="application/pdf",
                )
            )
            offer.calculations.append(
                OfferCalculation(
                    installment_number=1,
                    payment_date=date(2024, 2, 1),
                    opening_balance=Decimal("100000.00"),
                    principal_payment=Decimal("4000.00"),
                    interest_payment=Decimal("450.00"),
                    total_payment=Decimal("4450.00"),
                    closing_balance=Decimal("96000.00"),
                )
            )
            session.add(offer)
            session.commit()

            offer_id = offer.id
            assert offer_id and offer_id.startswith("OL")

        # Fresh session → forces a real read back from the database.
        with Session(engine) as session:
            fetched = session.get(OfferLetter, offer_id)
            assert fetched is not None
            assert fetched.customer_id == "C12345678"
            assert fetched.facility_id == "F1234567"

            # Enum columns persist as their string value and compare equal to
            # both the member and the raw value.
            assert fetched.status == OfferStatus.DRAFT
            assert fetched.status == "draft"
            assert fetched.repayment_type == RepaymentType.MONTHLY
            assert fetched.collateral_type == CollateralType.PROPERTY

            # Numeric money columns round-trip as Decimal.
            assert Decimal(str(fetched.principal_amount)) == Decimal("100000.00")
            assert Decimal(str(fetched.collateral_value)) == Decimal("250000.00")

            # Relationships load back.
            assert len(fetched.calculations) == 1
            assert fetched.calculations[0].installment_number == 1
            assert Decimal(str(fetched.calculations[0].total_payment)) == Decimal("4450.00")
            assert len(fetched.attachments) == 1
            assert fetched.attachments[0].filename == "offer.pdf"

            # repr still works on the persisted instance.
            assert "OfferLetter" in repr(fetched)

            # cascade="all, delete-orphan": deleting the parent removes children.
            session.delete(fetched)
            session.commit()

        with Session(engine) as session:
            assert session.get(OfferLetter, offer_id) is None
            assert session.query(OfferCalculation).count() == 0
            assert session.query(OfferAttachment).count() == 0
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
