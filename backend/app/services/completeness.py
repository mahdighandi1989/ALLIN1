"""Profile completeness — recompute a customer's completeness score and list the
fields that are still missing.

The Excel system computed this (ProfileGetCompleteness / ShowMissingFields) so the
KYC and Summary wizards only asked for what was actually absent (requirements A1 /
A25). Here it is a single server-side function: it inspects the structured profile
plus the related records (facilities, guarantors, securities, properties, FDs) and
returns a percentage + a human-readable list of what's missing, and persists the
percentage on the profile.
"""
from __future__ import annotations

from sqlalchemy import select, func

from app.models.crm import CustomerProfile
from app.models.customer import Customer
from app.models.facility import Facility
from app.models.guarantor import Guarantor
from app.models.security import Security
from app.models.profile_entities import MortgagedProperty, FixedDeposit

# Profile fields that count toward completeness (label, attribute).
_PROFILE_ITEMS = [
    ("Business type", "business_type"),
    ("Rating", "rating"),
    ("Trade licence no", "trade_license_no"),
    ("Trade licence expiry", "trade_license_expiry"),
    ("Passport no", "passport_no"),
    ("Passport expiry", "passport_expiry"),
    ("Emirates ID no", "emirates_id_no"),
    ("Emirates ID expiry", "emirates_id_expiry"),
    ("Visa no", "visa_no"),
    ("Tenancy no", "tenancy_no"),
]


async def recompute_completeness(db, account_no: str) -> dict:
    """Recompute completeness for an account, persist the % on the profile, and
    return ``{account_no, percent, filled, total, missing[]}``. Caller commits."""
    acc = (account_no or "").strip()
    cp = (
        await db.execute(select(CustomerProfile).where(CustomerProfile.account_no == acc))
    ).scalar_one_or_none()

    async def _count(model) -> int:
        q = select(func.count()).select_from(model).where(model.account_no == acc)
        if hasattr(model, "is_deleted"):
            q = q.where(model.is_deleted == False)  # noqa: E712
        return (await db.execute(q)).scalar() or 0

    cid = (
        await db.execute(select(Customer.id).where(Customer.account_no == acc))
    ).scalar_one_or_none()
    fac_count = 0
    if cid:
        fac_count = (
            await db.execute(
                select(func.count()).select_from(Facility).where(
                    Facility.customer_id == cid, Facility.is_deleted == False  # noqa: E712
                )
            )
        ).scalar() or 0

    guar = await _count(Guarantor)
    sec = await _count(Security)
    props = await _count(MortgagedProperty)
    fds = await _count(FixedDeposit)

    items: list[tuple[str, bool]] = [
        (label, bool(getattr(cp, attr, None)) if cp is not None else False)
        for label, attr in _PROFILE_ITEMS
    ]
    items.append(("At least one facility", fac_count > 0))
    items.append(("Guarantor or security cheque", guar > 0 or sec > 0))
    items.append(("Collateral (property or fixed deposit)", props > 0 or fds > 0))

    filled = sum(1 for _, ok in items if ok)
    total = len(items)
    percent = round(100 * filled / total) if total else 0
    missing = [label for label, ok in items if not ok]

    if cp is not None:
        cp.profile_completeness = f"{percent}%"

    return {
        "account_no": acc,
        "percent": percent,
        "filled": filled,
        "total": total,
        "missing": missing,
    }
