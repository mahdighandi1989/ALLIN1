"""run_expiry_scan must detect KYC-document expiry from CustomerProfile rows
WITHOUT loading every profile as a full ORM object.

Once the customer-listing import pushed customer_profiles to ~44k rows, the old
``select(CustomerProfile)).scalars().all()`` materialised all of them (with their
data_json) on every startup and OOM-killed the 512MB instance. The scan now
selects only the five KYC expiry-date columns and lets the DB filter out the
(vast majority of) profiles that carry none. These tests pin that behaviour:
the right alerts are still raised, and profiles without any expiry are ignored.
"""
from datetime import date, timedelta

from sqlalchemy import select

from app.models.crm import CustomerProfile, CustomTask
from app.services.expiry import run_expiry_scan


async def test_expiry_scan_flags_expiring_kyc_doc(db_session):
    soon = (date.today() + timedelta(days=10)).isoformat()
    # One profile with a passport expiring inside the window...
    db_session.add(CustomerProfile(account_no="600001", passport_expiry=soon))
    # ...amongst many "listing-style" profiles that carry NO expiry dates (the
    # common case the SQL filter must drop instead of materialising).
    for i in range(50):
        db_session.add(CustomerProfile(account_no=f"7000{i:02d}", branch="2533"))
    await db_session.commit()

    result = await run_expiry_scan(db_session, warning_days=90)

    assert result["documents"] >= 1
    # A High-priority alert task was raised for the expiring passport (and the
    # label/attr zip stays aligned with the selected columns).
    alerts = (
        await db_session.execute(
            select(CustomTask).where(CustomTask.account_no == "600001")
        )
    ).scalars().all()
    assert any("Passport" in (t.task_name or "") for t in alerts)

    # Profiles without any expiry date raised nothing.
    none_alerts = (
        await db_session.execute(
            select(CustomTask).where(CustomTask.account_no == "700000")
        )
    ).scalars().all()
    assert none_alerts == []


async def test_expiry_scan_no_profiles_is_noop(db_session):
    result = await run_expiry_scan(db_session, warning_days=30)
    assert result["documents"] == 0
    assert result["total"] == 0


async def test_expiring_documents_endpoint_filters_and_maps(db_session):
    """The /stats/expiring-documents endpoint now selects only the doc columns
    (not full rows); confirm it still returns correct, well-mapped alerts and
    ignores profiles with no expiry date."""
    from app.routers.stats import expiring_documents

    soon = (date.today() + timedelta(days=20)).isoformat()
    db_session.add(CustomerProfile(
        account_no="600002", customer_name="ACME LLC",
        passport_no="P-9", passport_expiry=soon,
    ))
    for i in range(30):  # listing-style profiles with no expiry → must be dropped
        db_session.add(CustomerProfile(account_no=f"7100{i:02d}", branch="2533"))
    await db_session.commit()

    res = await expiring_documents(db=db_session, days=90)

    assert res["total"] >= 1
    mine = [a for a in res["items"] if a["account_no"] == "600002"]
    assert mine and mine[0]["document"] == "Passport"
    assert mine[0]["number"] == "P-9"            # number column mapped correctly
    assert mine[0]["customer_name"] == "ACME LLC"
    assert "710000" not in {a["account_no"] for a in res["items"]}
