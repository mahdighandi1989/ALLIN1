"""Tests for Pydantic request-schema input validation (task 568f1abe).

Covers:
  AC#1 invalid input is rejected with HTTP 422,
  AC#2 every text field has a length limit,
  AC#3 sensitive fields (phone, account number, currency, tenor) enforce regex
       patterns, and free-text fields reject HTML/XSS payloads.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.facility import FacilityCreate, FacilityUpdate


# ---------------------------------------------------------------------------
# Schema-level (static) validation
# ---------------------------------------------------------------------------
class TestCustomerSchemaValidation:
    def test_valid_customer(self):
        c = CustomerCreate(
            account_no="ACC001",
            name="Acme Corp",
            phone="+971 50 123 4567",
            email="acme@example.com",
        )
        assert c.name == "Acme Corp"

    def test_optional_empty_values_allowed(self):
        # Existing clients submit "" for blank optional fields.
        c = CustomerCreate(name="Jane Doe", phone="", account_no="")
        assert c.name == "Jane Doe"

    @pytest.mark.parametrize("kwargs", [
        {"name": ""},                                   # empty required name
        {"name": "x" * 201},                            # name exceeds max_length
        {"name": "<script>alert(1)</script>"},          # XSS payload
        {"name": "ok", "phone": "abc"},                 # non-numeric phone
        {"name": "ok", "phone": "12"},                  # too few digits
        {"name": "ok", "email": "not-an-email"},        # invalid email
        {"name": "ok", "account_no": "<bad>"},          # invalid account chars
        {"name": "ok", "account_no": "x" * 51},         # account too long
    ])
    def test_invalid_customer_rejected(self, kwargs):
        with pytest.raises(ValidationError):
            CustomerCreate(**kwargs)

    def test_customer_update_invalid_rejected(self):
        with pytest.raises(ValidationError):
            CustomerUpdate(name="<x>")


class TestFacilitySchemaValidation:
    def test_valid_facility(self):
        f = FacilityCreate(customer_id="C1", amount=Decimal("50000"), currency="aed")
        assert f.currency == "AED"  # normalised to upper-case ISO code

    @pytest.mark.parametrize("kwargs", [
        {"customer_id": "C1", "amount": Decimal("0")},                  # not > 0
        {"customer_id": "C1", "amount": Decimal("-5")},                 # negative
        {"customer_id": "C1", "amount": Decimal("1e15")},              # too large
        {"customer_id": "", "amount": Decimal("5")},                   # empty id
        {"customer_id": "x" * 51, "amount": Decimal("5")},            # id too long
        {"customer_id": "C1", "amount": Decimal("5"), "currency": "DOLLAR"},
        {"customer_id": "C1", "amount": Decimal("5"), "tenor_months": "abc"},
        {"customer_id": "C1", "amount": Decimal("5"), "notes": "<img onerror=x>"},
        {"customer_id": "C1", "amount": Decimal("5"), "interest_rate": Decimal("150")},
    ])
    def test_invalid_facility_rejected(self, kwargs):
        with pytest.raises(ValidationError):
            FacilityCreate(**kwargs)

    def test_facility_update_invalid_rejected(self):
        with pytest.raises(ValidationError):
            FacilityUpdate(amount=Decimal("-1"))


# ---------------------------------------------------------------------------
# Static guarantees over the schema definitions (AC#2 / AC#3)
# ---------------------------------------------------------------------------
class TestSchemaConstraints:
    @pytest.mark.parametrize("model", [CustomerCreate, FacilityCreate, CustomerUpdate, FacilityUpdate])
    def test_all_text_fields_have_length_limit(self, model):
        """AC#2: every free-text string field exposes a maxLength in its schema.

        Numeric fields (Decimal -> rendered with a string variant), enums and
        date fields are intrinsically bounded and are skipped.
        """
        schema = model.model_json_schema()
        for name, prop in schema.get("properties", {}).items():
            variants = prop.get("anyOf", [prop])
            types = {v.get("type") for v in variants}
            # Skip numeric/decimal fields (their string form is not free text).
            if types & {"number", "integer"}:
                continue
            for v in variants:
                if v.get("type") != "string":
                    continue
                if "enum" in v or v.get("format") in {"date", "date-time"}:
                    continue  # enums/dates are intrinsically length-bounded
                assert "maxLength" in v, f"{model.__name__}.{name} string lacks maxLength"

    def test_sensitive_fields_have_patterns(self):
        """AC#3: sensitive fields reject malformed values (regex enforced)."""
        with pytest.raises(ValidationError):
            CustomerCreate(name="ok", phone="not-a-phone!!")
        with pytest.raises(ValidationError):
            FacilityCreate(customer_id="C1", amount=Decimal("5"), currency="XX")
        with pytest.raises(ValidationError):
            FacilityCreate(customer_id="C1", amount=Decimal("5"), tenor_months="12months")


# ---------------------------------------------------------------------------
# API-level (AC#1: invalid input -> HTTP 422)
# ---------------------------------------------------------------------------
class TestApiValidation:
    async def test_create_customer_invalid_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """AC#1: posting an invalid customer body returns 422."""
        response = await client.post(
            "/api/customers/",
            json={"name": "<script>alert(1)</script>", "phone": "123"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_customer_missing_name_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/customers/", json={"account_no": "ACC999"}, headers=auth_headers
        )
        assert response.status_code == 422
