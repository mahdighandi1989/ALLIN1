"""Reusable validators and constrained types for request (write) schemas.

Centralises input validation so every write schema consistently enforces:
  - length limits on text fields,
  - regex patterns on sensitive fields (phone, account number, currency, tenor),
  - rejection of HTML/script payloads and control characters (basic XSS / data
    integrity hardening) — invalid input raises a ValueError which FastAPI turns
    into an HTTP 422 response.

Optional fields tolerate ``None`` and empty string ("") so existing clients that
submit blank optional values keep working; non-empty values are fully validated.
"""
import re
from typing import Annotated, Optional

from pydantic import AfterValidator

# ASCII control characters are never allowed in free-text fields (tab/newline/CR
# are permitted so multi-line notes keep working).
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PHONE_ALLOWED_RE = re.compile(r"^\+?[0-9\s\-()]+$")
_ACCOUNT_NO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-/_]*$")
_CURRENCY_RE = re.compile(r"^[A-Za-z]{3}$")
_TENOR_RE = re.compile(r"^[0-9]{1,4}$")


def reject_unsafe_text(v: Optional[str]) -> Optional[str]:
    """Reject strings containing HTML angle brackets or control characters.

    This is a lightweight defence against stored-XSS payloads entering the
    database via free-text fields. It does not mutate valid input.
    """
    if v is None or not isinstance(v, str):
        return v
    if "<" in v or ">" in v:
        raise ValueError("must not contain '<' or '>' characters")
    if _CONTROL_RE.search(v):
        raise ValueError("must not contain control characters")
    return v


def validate_phone(v: Optional[str]) -> Optional[str]:
    """Validate an (optional) international-friendly phone number."""
    if v is None or v == "":
        return v
    s = v.strip()
    if s == "":
        return s
    if not _PHONE_ALLOWED_RE.match(s):
        raise ValueError("phone may contain only digits, spaces and + - ( )")
    digits = re.sub(r"\D", "", s)
    if not (7 <= len(digits) <= 15):
        raise ValueError("phone must contain between 7 and 15 digits")
    return s


def validate_account_no(v: Optional[str]) -> Optional[str]:
    """Validate an (optional) account/customer identifier."""
    if v is None or v == "":
        return v
    s = v.strip()
    if not _ACCOUNT_NO_RE.match(s):
        raise ValueError("account number may contain only letters, digits and - / _")
    return s


def validate_currency(v: Optional[str]) -> Optional[str]:
    """Validate and normalise a 3-letter ISO currency code (e.g. AED)."""
    if v is None or v == "":
        return v
    s = v.strip().upper()
    if not _CURRENCY_RE.match(s):
        raise ValueError("currency must be a 3-letter ISO code (e.g. AED)")
    return s


def validate_tenor_months(v: Optional[str]) -> Optional[str]:
    """Validate an (optional) tenor expressed in months (digits only)."""
    if v is None or v == "":
        return v
    s = v.strip()
    if not _TENOR_RE.match(s):
        raise ValueError("tenor_months must be 1-4 digits")
    return s


# Reusable annotated types — combine these with Field(min_length/max_length=...)
# in the schema definitions to also enforce length limits.
SafeText = Annotated[str, AfterValidator(reject_unsafe_text)]
OptionalSafeText = Annotated[Optional[str], AfterValidator(reject_unsafe_text)]
Phone = Annotated[Optional[str], AfterValidator(validate_phone)]
AccountNo = Annotated[Optional[str], AfterValidator(validate_account_no)]
Currency = Annotated[str, AfterValidator(validate_currency)]
OptionalCurrency = Annotated[Optional[str], AfterValidator(validate_currency)]
TenorMonths = Annotated[Optional[str], AfterValidator(validate_tenor_months)]
