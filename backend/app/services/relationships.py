"""Cross-account relationships (e.g. who guarantees whom), derived generically.

For an account A this answers two questions, driven by the collateral registry's
``relation_account_attr`` so future relationship types participate automatically:

  * GIVEN    — A is the related party (e.g. A is the guarantor) for other
               accounts. Lets A's own profile state precisely which accounts it
               has guaranteed / is tied to.
  * RECEIVED — other accounts are the related party for A (e.g. A is guaranteed
               by them).

Each side resolves the counterpart account_no to a customer id/name so the UI
can link straight to that profile from anywhere the name appears.
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.services.collateral import relationship_entries


def _clean(v) -> str:
    return (v or "").strip() if isinstance(v, str) else (str(v).strip() if v is not None else "")


async def _customer_map(db: AsyncSession, accounts: set[str]) -> dict[str, dict]:
    accs = [a for a in accounts if a]
    if not accs:
        return {}
    rows = (
        await db.execute(
            sa.select(Customer.account_no, Customer.id, Customer.name).where(
                Customer.account_no.in_(accs), Customer.is_deleted == False  # noqa: E712
            )
        )
    ).all()
    return {acc: {"customer_id": cid, "name": name} for acc, cid, name in rows}


async def relationships_for_account(db: AsyncSession, account_no: str) -> dict:
    """Return {given: [...], received: [...]} for ``account_no``."""
    account_no = _clean(account_no)
    given: list[dict] = []
    received: list[dict] = []
    if not account_no:
        return {"given": given, "received": received}

    needed_accounts: set[str] = set()
    raw_given: list[tuple] = []     # (entry, row)
    raw_received: list[tuple] = []

    for entry in relationship_entries():
        model = entry.model
        rel_col = getattr(model, entry.relation_account_attr)
        name_col = getattr(model, entry.relation_name_attr) if entry.relation_name_attr else None

        base = []
        if _has_deleted(model):
            base.append(model.is_deleted == False)  # noqa: E712

        # GIVEN: rows where the related account IS this account (A is the guarantor).
        given_rows = (
            await db.execute(sa.select(model).where(rel_col == account_no, *base))
        ).scalars().all()
        for r in given_rows:
            raw_given.append((entry, r))
            needed_accounts.add(_clean(getattr(r, "account_no", "")))

        # RECEIVED: rows owned by this account that name a related party.
        recv_rows = (
            await db.execute(
                sa.select(model).where(
                    model.account_no == account_no, rel_col.isnot(None), rel_col != "", *base
                )
            )
        ).scalars().all()
        for r in recv_rows:
            raw_received.append((entry, r))
            needed_accounts.add(_clean(getattr(r, entry.relation_account_attr, "")))

    cmap = await _customer_map(db, needed_accounts)

    for entry, r in raw_given:
        owner_acc = _clean(getattr(r, "account_no", ""))
        info = cmap.get(owner_acc, {})
        given.append({
            "relation": entry.relation_label or entry.key,
            "kind": entry.key,
            "id": getattr(r, "id", None),
            "counterparty_account": owner_acc,
            "counterparty_name": getattr(r, "customer_name", None) or info.get("name"),
            "counterparty_customer_id": info.get("customer_id"),
            "detail": _relation_detail(entry, r),
        })

    for entry, r in raw_received:
        rel_acc = _clean(getattr(r, entry.relation_account_attr, ""))
        info = cmap.get(rel_acc, {})
        name_col = entry.relation_name_attr
        received.append({
            "relation": entry.relation_label or entry.key,
            "kind": entry.key,
            "id": getattr(r, "id", None),
            "counterparty_account": rel_acc,
            "counterparty_name": (getattr(r, name_col, None) if name_col else None) or info.get("name"),
            "counterparty_customer_id": info.get("customer_id"),
            "detail": _relation_detail(entry, r),
        })

    return {"given": given, "received": received}


def _has_deleted(model) -> bool:
    return "is_deleted" in model.__table__.columns


def _relation_detail(entry, row) -> dict:
    """A few descriptive fields per relation kind (best-effort, never raises)."""
    out = {}
    for f in ("cheque_no", "cheque_amount", "issuing_bank", "share", "amount"):
        if hasattr(row, f):
            v = getattr(row, f)
            if v not in (None, ""):
                try:
                    out[f] = float(v) if f in ("cheque_amount", "amount") else v
                except (TypeError, ValueError):
                    out[f] = v
    return out
