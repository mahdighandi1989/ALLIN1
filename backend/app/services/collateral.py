"""Central registry of account_no-keyed "collateral / child" entities.

This is the single source of truth for *which* per-customer child records exist
(mortgaged properties, guarantors, fixed deposits, partners, …). The orphan
reconcile, the facility-detail aggregation, and any future cross-entity feature
iterate this registry instead of hard-coding each table — so wiring a NEW child
entity into the credit-file graph is a one-line addition here, and it instantly
participates in:

  * orphan → stub-customer reconciliation (anything with ``account_no``);
  * "show under the facility it secures" (anything with ``facility_id``).

Conventions a child model should follow to be a first-class collateral entity:
  * ``account_no``   — owning customer key (required to participate at all);
  * ``customer_name``— denormalised name hint (optional but recommended);
  * ``facility_id``  — optional link to a specific facility;
  * ``is_deleted``   — soft-delete flag.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guarantor import Guarantor
from app.models.profile_entities import MortgagedProperty, FixedDeposit, Partner


@dataclass(frozen=True)
class CollateralEntry:
    key: str        # stable key used in API payloads (e.g. "properties")
    model: type     # the ORM model
    label: str      # human label (UI/back-office)


# The registry. Append a line here to enrol a future child entity.
REGISTRY: list[CollateralEntry] = [
    CollateralEntry("properties", MortgagedProperty, "Mortgaged properties"),
    CollateralEntry("guarantors", Guarantor, "Guarantors"),
    CollateralEntry("fixed_deposits", FixedDeposit, "Fixed deposits"),
    CollateralEntry("partners", Partner, "Partners / shareholders"),
]


def _has_col(model: type, name: str) -> bool:
    return name in model.__table__.columns


def account_keyed_models() -> list[type]:
    """Models that carry an ``account_no`` (participate in orphan reconcile)."""
    return [e.model for e in REGISTRY if _has_col(e.model, "account_no")]


def facility_linked_entries() -> list[CollateralEntry]:
    """Registry entries whose model can be pinned to a specific facility."""
    return [e for e in REGISTRY if _has_col(e.model, "facility_id")]


def serialize(obj) -> dict:
    """JSON-safe view of a child row (Decimal -> float, drop noisy columns)."""
    out = {}
    for col in obj.__table__.columns:
        if col.name in ("created_at",):
            continue
        v = getattr(obj, col.name)
        out[col.name] = float(v) if isinstance(v, Decimal) else v
    return out


async def collateral_for_facility(db: AsyncSession, facility_id: str) -> dict:
    """Return every collateral record pinned to ``facility_id``, grouped by key.

    Iterates the registry, so a newly-registered entity automatically shows up
    under the facility it secures with no extra code here or in the router.
    """
    result: dict[str, list[dict]] = {}
    if not facility_id:
        return {e.key: [] for e in facility_linked_entries()}
    for entry in facility_linked_entries():
        model = entry.model
        conds = [model.facility_id == facility_id]
        if _has_col(model, "is_deleted"):
            conds.append(model.is_deleted == False)  # noqa: E712
        rows = (await db.execute(sa.select(model).where(*conds))).scalars().all()
        result[entry.key] = [serialize(r) for r in rows]
    return result
