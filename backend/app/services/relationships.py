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

    # First-class explicit links (letters, AI-extractions, manual) — generic for
    # EVERY subject, each carrying its kind + the exact recorded reason. A link is
    # stored once but surfaces on BOTH profiles (given on the owning side,
    # received on the related side).
    from app.models.customer_link_rel import CustomerLink

    link_given = (
        await db.execute(
            sa.select(CustomerLink).where(
                CustomerLink.account_no == account_no, CustomerLink.is_deleted == False  # noqa: E712
            )
        )
    ).scalars().all()
    link_recv = (
        await db.execute(
            sa.select(CustomerLink).where(
                CustomerLink.related_account == account_no, CustomerLink.is_deleted == False  # noqa: E712
            )
        )
    ).scalars().all()
    for l in link_given:
        needed_accounts.add(_clean(l.related_account))
    for l in link_recv:
        needed_accounts.add(_clean(l.account_no))

    cmap = await _customer_map(db, needed_accounts)

    for l, mine, other_acc in (
        [(l, "given", _clean(l.related_account)) for l in link_given]
        + [(l, "received", _clean(l.account_no)) for l in link_recv]
    ):
        info = cmap.get(other_acc, {})
        item = {
            "relation": KIND_FA.get(l.kind, l.kind), "kind": f"link:{l.kind}", "id": l.id,
            "counterparty_account": other_acc, "counterparty_name": info.get("name"),
            "counterparty_customer_id": info.get("customer_id"),
            "detail": {"reason": l.reason, "source": l.source, "source_ref": l.source_ref},
        }
        (given if mine == "given" else received).append(item)

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


KIND_FA = {"guarantor": "ضامن", "letter": "نامه‌نگاری", "co_signer": "امضای مشترک",
           "family": "نسبت خانوادگی", "business_partner": "شریک تجاری", "other": "مرتبط"}
VALID_LINK_KINDS = set(KIND_FA)


async def ensure_link(
    db: AsyncSession, account_no: str, related_account: str, *, kind: str, reason: str,
    source: str = "manual", source_ref: str = "", created_by: str = "",
):
    """Create an explicit profile↔profile link once (idempotent, direction-agnostic).

    The SAME pair+kind (either direction) never duplicates: an existing live link
    is returned with its reason kept (first recorded reason wins; a new distinct
    reason is appended). Does NOT commit — caller owns the transaction."""
    from app.models.customer_link_rel import CustomerLink

    a, b = _clean(account_no), _clean(related_account)
    k = (kind or "other").strip() if (kind or "").strip() in VALID_LINK_KINDS else "other"
    why = " ".join((reason or "").split())[:900]
    if not a or not b or a == b or not why:
        return None
    existing = (
        await db.execute(
            sa.select(CustomerLink).where(
                CustomerLink.kind == k, CustomerLink.is_deleted == False,  # noqa: E712
                sa.or_(
                    sa.and_(CustomerLink.account_no == a, CustomerLink.related_account == b),
                    sa.and_(CustomerLink.account_no == b, CustomerLink.related_account == a),
                ),
            )
        )
    ).scalars().first()
    if existing is not None:
        if why not in (existing.reason or ""):
            existing.reason = ((existing.reason or "") + " | " + why)[:2000]
        return existing
    link = CustomerLink(account_no=a, related_account=b, kind=k, reason=why,
                        source=source[:40], source_ref=(source_ref or "")[:80],
                        created_by=(created_by or "")[:80])
    db.add(link)
    return link


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
