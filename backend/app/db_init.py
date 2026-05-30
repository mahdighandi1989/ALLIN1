"""Self-healing database bootstrap.

Production databases predate several model changes (e.g. ``users.is_admin``,
the ``lg``/``pending`` enum values), and the deploy's ``alembic upgrade head``
swallows errors — so the live schema can silently drift from the models and make
every query 500. This module brings the database in line with the SQLAlchemy
models on every startup, independent of Alembic:

* creates any missing tables / enum types,
* adds any missing columns (with sensible defaults so existing rows stay valid),
* adds any missing enum values,
* seeds a realistic set of demo banking data when the database is empty, so the
  dashboard is populated instead of showing zeros.

Every step is idempotent and individually guarded so a failure can never crash
startup.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import inspect, text

from app.database import Base, engine, AsyncSessionLocal
# Import models so they are registered on Base.metadata.
from app.models.user import User  # noqa: F401
from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus

logger = logging.getLogger(__name__)

# Enum (postgres type name -> allowed values) derived from the models.
_ENUMS = {
    "accounttype": [e.value for e in AccountType],
    "customerstatus": [e.value for e in CustomerStatus],
    "facilitytype": [e.value for e in FacilityType],
    "facilitystatus": [e.value for e in FacilityStatus],
}


def _default_sql(col: sa.Column) -> str | None:
    """Best-effort SQL literal for backfilling a newly-added column."""
    d = col.default
    if d is not None and getattr(d, "is_scalar", False):
        val = d.arg
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float, Decimal)):
            return str(val)
        if isinstance(val, str):
            return "'" + val.replace("'", "''") + "'"
    t = col.type
    if isinstance(t, sa.Boolean):
        return "false"
    if isinstance(t, (sa.Integer, sa.Numeric)):
        return "0"
    if isinstance(t, (sa.String, sa.Text)):
        return "''"
    return None


def _add_missing_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        db_columns = inspector.get_columns(table.name)
        existing_cols = {c["name"] for c in db_columns}
        model_cols = {c.name for c in table.columns}

        # 1) Add columns the model defines but the live table is missing.
        for col in table.columns:
            if col.name in existing_cols:
                continue
            coltype = col.type.compile(dialect=sync_conn.dialect)
            ddl = (
                f'ALTER TABLE "{table.name}" '
                f'ADD COLUMN IF NOT EXISTS "{col.name}" {coltype}'
            )
            default = _default_sql(col)
            if default is not None:
                ddl += f" DEFAULT {default}"
            logger.info("schema-sync: %s", ddl)
            sync_conn.execute(text(ddl))

        # 2) Relax NOT NULL on columns the live table requires but the model does
        #    NOT know about (e.g. a legacy ``users.role``). Otherwise every INSERT
        #    from this codebase — which never sets those columns — would fail.
        for db_col in db_columns:
            name = db_col["name"]
            if name in model_cols:
                continue
            if db_col.get("nullable", True) or db_col.get("default") is not None:
                continue
            try:
                logger.info(
                    "schema-sync: relaxing NOT NULL on unknown column %s.%s",
                    table.name, name,
                )
                sync_conn.execute(
                    text(f'ALTER TABLE "{table.name}" ALTER COLUMN "{name}" DROP NOT NULL')
                )
            except Exception as exc:  # pragma: no cover - depends on live DB
                logger.warning(
                    "schema-sync: could not relax %s.%s: %s", table.name, name, exc
                )


async def ensure_schema() -> None:
    """Create missing tables/columns/enum values so the schema matches the models."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("schema-sync: create_all failed: %s", exc)

    if engine.dialect.name != "postgresql":
        return  # SQLite (tests) gets a complete schema from create_all.

    # Normalise enum labels. Legacy databases stored enum *names* (UPPERCASE,
    # e.g. 'CORPORATE'); the models now use the lowercase value ('corporate').
    # Rename any legacy UPPERCASE label to its lowercase form, then ensure every
    # model value exists. Both are idempotent and need AUTOCOMMIT.
    try:
        async with engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            # Existing labels per enum type.
            existing = {}
            for enum_name in _ENUMS:
                rows = (
                    await conn.execute(
                        text(
                            "SELECT e.enumlabel FROM pg_enum e "
                            "JOIN pg_type t ON t.oid = e.enumtypid "
                            "WHERE t.typname = :n"
                        ).bindparams(n=enum_name)
                    )
                ).all()
                existing[enum_name] = {r[0] for r in rows}

            for enum_name, values in _ENUMS.items():
                labels = existing.get(enum_name, set())
                for value in values:
                    upper = value.upper()
                    # Rename a legacy UPPERCASE label to the lowercase value.
                    if value not in labels and upper in labels:
                        await conn.execute(
                            text(f"ALTER TYPE {enum_name} RENAME VALUE '{upper}' TO '{value}'")
                        )
                        labels.discard(upper)
                        labels.add(value)
                    # Otherwise make sure the value exists.
                    elif value not in labels:
                        await conn.execute(
                            text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")
                        )
                        labels.add(value)
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.warning("schema-sync: enum value sync skipped: %s", exc)

    # Add any missing columns.
    try:
        async with engine.begin() as conn:
            await conn.run_sync(_add_missing_columns)
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.error("schema-sync: add-missing-columns failed: %s", exc)


# --- demo data ---------------------------------------------------------------
def _seed_rows():
    """Return (customers, facilities) sample data for an empty database."""
    today = date.today()
    customers = [
        Customer(account_no="AE-100201", name="Emirates Trading LLC",
                 account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE,
                 email="treasury@emiratestrading.ae", phone="+97142250100",
                 branch="Dubai Main", relationship_manager="N. Haddad"),
        Customer(account_no="AE-100202", name="Al Futtaim Industries",
                 account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE,
                 email="finance@alfuttaim.ae", phone="+97143330200",
                 branch="Dubai Main", relationship_manager="N. Haddad"),
        Customer(account_no="AE-100203", name="Gulf Tech FZE",
                 account_type=AccountType.SME, status=CustomerStatus.ACTIVE,
                 email="ar@gulftech.ae", phone="+97142509900",
                 branch="Jebel Ali", relationship_manager="S. Qassimi"),
        Customer(account_no="AE-100204", name="Ahmed Al Mansoori",
                 account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE,
                 email="a.mansoori@gmail.com", phone="+971501234567",
                 branch="Abu Dhabi", relationship_manager="L. Farouk"),
        Customer(account_no="AE-100205", name="Fatima Holdings",
                 account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE,
                 email="cfo@fatimaholdings.ae", phone="+97126667788",
                 branch="Abu Dhabi", relationship_manager="L. Farouk"),
        Customer(account_no="AE-100206", name="Desert Rose Trading",
                 account_type=AccountType.SME, status=CustomerStatus.ACTIVE,
                 email="accounts@desertrose.ae", phone="+97143001212",
                 branch="Sharjah", relationship_manager="S. Qassimi"),
        Customer(account_no="AE-100207", name="Sara Abdullah",
                 account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE,
                 email="sara.abdullah@outlook.com", phone="+971559876543",
                 branch="Dubai Main", relationship_manager="L. Farouk"),
        Customer(account_no="AE-100208", name="Khalid Enterprises",
                 account_type=AccountType.CORPORATE, status=CustomerStatus.INACTIVE,
                 email="ops@khalident.ae", phone="+97142228899",
                 branch="Jebel Ali", relationship_manager="N. Haddad"),
    ]

    def fac(cust, ftype, amount, outstanding, rate, status, expiry_days, name,
            risk="low", start_days_ago=365):
        return Facility(
            customer=cust, facility_type=ftype, name=name,
            amount=Decimal(amount), outstanding=Decimal(outstanding),
            currency="AED", interest_rate=Decimal(rate), status=status,
            start_date=today - timedelta(days=start_days_ago),
            expiry_date=today + timedelta(days=expiry_days),
            end_date=today + timedelta(days=expiry_days),
            risk_rating=risk, purpose="Working capital",
        )

    # Varied start dates + risk ratings give the dashboard a realistic trend line
    # and a meaningful risk-distribution chart.
    facilities = [
        fac(customers[0], FacilityType.LOAN, "25000000", "18500000", "6.25",
            FacilityStatus.ACTIVE, 540, "Term Loan A", risk="low", start_days_ago=150),
        fac(customers[0], FacilityType.OVERDRAFT, "5000000", "3200000", "8.5",
            FacilityStatus.ACTIVE, 20, "Working Capital OD", risk="medium", start_days_ago=95),
        fac(customers[1], FacilityType.LC, "12000000", "12000000", "4.0",
            FacilityStatus.ACTIVE, 25, "Import LC", risk="low", start_days_ago=60),
        fac(customers[1], FacilityType.LOAN, "40000000", "31000000", "5.75",
            FacilityStatus.ACTIVE, 900, "Syndicated Term Loan", risk="medium", start_days_ago=130),
        fac(customers[2], FacilityType.OVERDRAFT, "1500000", "900000", "9.0",
            FacilityStatus.ACTIVE, 200, "SME Overdraft", risk="high", start_days_ago=40),
        fac(customers[3], FacilityType.LOAN, "850000", "640000", "7.5",
            FacilityStatus.ACTIVE, 1200, "Auto Loan", risk="low", start_days_ago=20),
        fac(customers[4], FacilityType.LG, "8000000", "8000000", "3.5",
            FacilityStatus.ACTIVE, 15, "Performance Guarantee", risk="medium", start_days_ago=110),
        fac(customers[4], FacilityType.LOAN, "30000000", "30000000", "6.0",
            FacilityStatus.PENDING, 700, "Capex Facility", risk="high", start_days_ago=10),
        fac(customers[5], FacilityType.LC, "2200000", "2200000", "4.25",
            FacilityStatus.ACTIVE, 60, "Sight LC", risk="low", start_days_ago=75),
        fac(customers[6], FacilityType.LOAN, "500000", "120000", "8.0",
            FacilityStatus.CLOSED, -30, "Personal Loan", risk="low", start_days_ago=300),
    ]
    return customers, facilities


async def seed_sample_data() -> None:
    """Populate realistic demo data when the customers table is empty."""
    try:
        async with AsyncSessionLocal() as session:
            count = (await session.execute(sa.select(sa.func.count(Customer.id)))).scalar()
            if count and count > 0:
                return  # already has data
            customers, facilities = _seed_rows()
            session.add_all(customers)
            await session.flush()  # assign customer ids for FK
            session.add_all(facilities)
            await session.flush()
            offers = _seed_offers(customers)
            if offers:
                session.add_all(offers)
            await session.commit()
            logger.info(
                "Seeded demo banking data: %s customers, %s facilities, %s offer letters",
                len(customers), len(facilities), len(offers),
            )
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.error("Demo data seeding skipped: %s", exc)


def _seed_offers(customers):
    """Build a couple of demo offer letters (with computed repayment totals)."""
    try:
        from datetime import date, timedelta
        from decimal import Decimal
        from app.models.offer_letter import OfferLetter, OfferStatus, RepaymentType
        from app.services.amortization import generate_schedule, schedule_totals

        today = date.today()

        def offer(cust, principal, rate, tenor, status, name_purpose, rtype="monthly", grace=0):
            o = OfferLetter(
                customer_id=cust.id,
                offer_date=today - timedelta(days=10),
                expiry_date=today + timedelta(days=30),
                status=status,
                principal_amount=Decimal(principal),
                currency="AED",
                interest_rate=Decimal(rate),
                tenor_months=tenor,
                grace_period_months=grace,
                repayment_type=rtype,
                purpose_of_facility=name_purpose,
            )
            totals = schedule_totals(
                generate_schedule(
                    Decimal(principal), Decimal(rate), tenor,
                    repayment_type=rtype, grace_period_months=grace, start=o.offer_date,
                )
            )
            o.monthly_installment = totals["monthly_installment"]
            o.total_repayment_amount = totals["total_repayment_amount"]
            return o

        return [
            offer(customers[0], "15000000", "6.5", 36, OfferStatus.SENT, "Fleet expansion term loan"),
            offer(customers[1], "8000000", "5.75", 24, OfferStatus.APPROVED, "Working capital facility", grace=3),
            offer(customers[2], "1200000", "8.0", 18, OfferStatus.DRAFT, "SME growth loan"),
            offer(customers[4], "20000000", "6.0", 48, OfferStatus.PENDING_APPROVAL, "Capex financing"),
        ]
    except Exception as exc:  # pragma: no cover
        logger.error("Offer-letter seeding skipped: %s", exc)
        return []


async def seed_admin_user() -> None:
    """Create a bootstrap admin account if the users table has no users.

    Ensures the app is loginable out of the box once AUTH_DISABLED is turned off.
    """
    try:
        from app.config import settings
        from app.models.user import User
        from app.utils.security import hash_password

        async with AsyncSessionLocal() as session:
            count = (await session.execute(sa.select(sa.func.count(User.id)))).scalar()
            if count and count > 0:
                return
            session.add(
                User(
                    username=str(settings.DEFAULT_ADMIN_USERNAME).lower(),
                    email=str(settings.DEFAULT_ADMIN_EMAIL).lower(),
                    hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    full_name="Administrator",
                    is_active=True,
                    is_admin=True,
                )
            )
            await session.commit()
            logger.info(
                "Seeded bootstrap admin user '%s'", settings.DEFAULT_ADMIN_USERNAME
            )
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.error("Admin user seeding skipped: %s", exc)


async def refresh_expiry_notifications() -> None:
    """Create a broadcast notification summarising facilities expiring soon.

    Idempotent per day: skips if an 'expiry' broadcast was already created today.
    """
    try:
        from datetime import date, timedelta, datetime
        from app.models.facility import Facility
        from app.models.notification import Notification

        async with AsyncSessionLocal() as session:
            today = date.today()
            horizon = today + timedelta(days=30)
            expiry = sa.func.coalesce(Facility.expiry_date, Facility.end_date)
            count = (
                await session.execute(
                    sa.select(sa.func.count(Facility.id)).where(
                        Facility.is_deleted == False,
                        expiry >= today,
                        expiry <= horizon,
                    )
                )
            ).scalar() or 0
            if count == 0:
                return

            # Skip if we already posted an expiry broadcast today.
            existing = (
                await session.execute(
                    sa.select(sa.func.count(Notification.id)).where(
                        Notification.category == "facility",
                        Notification.user_id.is_(None),
                        Notification.created_at >= datetime.combine(today, datetime.min.time()),
                    )
                )
            ).scalar() or 0
            if existing:
                return

            session.add(
                Notification(
                    user_id=None,
                    level="warning",
                    title=f"{count} facilities expiring within 30 days",
                    message="Review the dashboard watch-list for upcoming expiries.",
                    link="/dashboard",
                    category="facility",
                    is_read=False,
                )
            )
            await session.commit()
            logger.info("Created expiry notification for %s facilities", count)
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.error("Expiry notification refresh skipped: %s", exc)


async def init_database() -> None:
    """Run schema sync + demo seeding (called once at startup)."""
    await ensure_schema()
    await seed_sample_data()
    await seed_admin_user()
    await refresh_expiry_notifications()
