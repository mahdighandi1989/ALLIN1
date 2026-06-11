"""Link collateral/child records to a customer profile, auto-creating a stub
customer when an orphan ``account_no`` has no profile yet.

A mortgaged property (or any account_no-keyed child) always belonged to some
customer + facility, even if that customer was never entered in the panel. So
instead of leaving such rows visible only in their own list ("islands"), we
materialise a minimal Customer profile for the account_no the first time we see
it. The profile is flagged as auto-created so an operator can later complete it.
"""
from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer

logger = logging.getLogger(__name__)

# Marker stored in the stub's notes so the UI/operator knows it needs completing.
STUB_NOTE = "↪ پروفایلِ خودکار از روی وثیقه/ملک. لطفاً اطلاعات مشتری را کامل کنید."


def _clean_account(account_no: str) -> str:
    return (account_no or "").strip()


async def find_customer_by_account(db: AsyncSession, account_no: str) -> Customer | None:
    acc = _clean_account(account_no)
    if not acc:
        return None
    return (
        await db.execute(
            sa.select(Customer).where(
                Customer.account_no == acc, Customer.is_deleted == False  # noqa: E712
            )
        )
    ).scalar_one_or_none()


async def ensure_customer(
    db: AsyncSession, account_no: str, name_hint: str | None = None
) -> Customer | None:
    """Return the customer for ``account_no``, creating a stub profile if missing.

    Does NOT commit — the caller commits as part of its own unit of work. Returns
    None only when ``account_no`` is blank.
    """
    acc = _clean_account(account_no)
    if not acc:
        return None
    existing = await find_customer_by_account(db, acc)
    if existing:
        return existing
    name = (name_hint or "").strip() or f"(نامشخص) {acc}"
    stub = Customer(account_no=acc, name=name[:200], notes=STUB_NOTE)
    db.add(stub)
    await db.flush()  # assign PK without ending the caller's transaction
    logger.info("Auto-created stub customer for orphan account_no=%s", acc)
    return stub


async def reconcile_orphan_collateral(db: AsyncSession | None = None) -> int:
    """Create stub profiles for every collateral account_no that lacks a customer.

    Scans every account_no-keyed entity in the collateral registry (properties,
    guarantors, fixed deposits, partners, and anything added there later) so
    nothing is stranded outside a customer profile. Best effort and idempotent;
    returns the number of stubs created. Opens its own session when one isn't
    supplied (so it can run from startup).
    """
    from app.database import AsyncSessionLocal
    from app.services.collateral import account_keyed_models

    own_session = db is None
    session = db or AsyncSessionLocal()
    created = 0
    try:
        # Gather (account_no -> a name hint) across all registered child tables.
        hints: dict[str, str] = {}
        for model in account_keyed_models():
            name_col = getattr(model, "customer_name", None)
            cols = [model.account_no] + ([name_col] if name_col is not None else [])
            rows = (await session.execute(sa.select(*cols))).all()
            for row in rows:
                acc = _clean_account(row[0])
                if not acc:
                    continue
                hint = (row[1] if len(row) > 1 and row[1] else "")
                if acc not in hints or (hint and not hints[acc]):
                    hints[acc] = hint

        if not hints:
            return 0

        existing = set(
            (
                await session.execute(
                    sa.select(Customer.account_no).where(
                        Customer.account_no.in_(list(hints.keys()))
                    )
                )
            ).scalars().all()
        )
        for acc, hint in hints.items():
            if acc in existing:
                continue
            await ensure_customer(session, acc, hint)
            created += 1

        if created:
            await session.commit()
            logger.info("Reconciled %d orphan collateral account(s) into stub profiles", created)
        return created
    except Exception as exc:  # pragma: no cover - best-effort backfill
        logger.error("Orphan collateral reconcile skipped: %s", exc)
        try:
            await session.rollback()
        except Exception:
            pass
        return created
    finally:
        if own_session:
            await session.close()
