"""Tests for the database-cleanup (de-dup) engine + admin API."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.customer import Customer
from app.models.guarantor import Guarantor
from app.models.profile_entities import MortgagedProperty, Partner, FixedDeposit
from app.models.audit_log import AuditLog
from app.models.cleanup_run import CleanupRun
from app.models.notification import Notification
from app.models.system_setting import SystemSetting
from app.services import db_cleanup


async def _seed(db):
    acc = "500100"
    db.add(Customer(id="C500100", account_no=acc, name="Test Co"))
    # properties: two duplicates by plate (one more complete = keeper) + one unique
    db.add(MortgagedProperty(id="P1", account_no=acc, plate_no="A-1", address="Zayed Rd", valuation=None))
    db.add(MortgagedProperty(id="P2", account_no=acc, plate_no="A-1", address="Zayed Rd", owner="Ali", valuation=100))  # more complete
    db.add(MortgagedProperty(id="P3", account_no=acc, plate_no="B-2", address="Other"))  # unique
    # guarantors: two with same cheque_no (dup) + one different
    db.add(Guarantor(id="G1", account_no=acc, guarantor_name="Ali Hammadi", cheque_no="CH1"))
    db.add(Guarantor(id="G2", account_no=acc, guarantor_name="Ali Hammadi", cheque_no="CH1", issuing_bank="ADCB"))  # keeper
    db.add(Guarantor(id="G3", account_no=acc, guarantor_name="Sara", cheque_no="CH9"))  # unique
    # partners: same person by name (dup)
    db.add(Partner(id="PT1", account_no=acc, name="Yousef Alhammadi"))
    db.add(Partner(id="PT2", account_no=acc, name="Yousef Mohamed Alhammadi", nationality="UAE"))  # keeper (subset match)
    # fixed deposit: unique (no dup)
    db.add(FixedDeposit(id="FD1", account_no=acc, fd_number="FD-777"))
    await db.commit()
    return acc


@pytest.mark.asyncio
async def test_scan_detects_duplicates_without_changing_data(db_session):
    acc = await _seed(db_session)
    report = await db_cleanup.scan(db_session)
    c = report["counts"]
    assert c["properties"] == 1   # one removal (P1 or P2)
    assert c["guarantors"] == 1   # one removal
    assert c["partners"] == 1     # one removal
    assert c["fixed_deposits"] == 0
    assert c["total_removals"] == 3
    # keeper for properties is the more complete row (P2 has owner+valuation)
    prop_groups = report["groups"]["properties"]
    assert len(prop_groups) == 1
    assert prop_groups[0]["keeper"]["id"] == "P2"
    assert prop_groups[0]["account_no"] == acc
    # scan changed NOTHING
    live = (await db_session.execute(select(MortgagedProperty).where(MortgagedProperty.is_deleted == False))).scalars().all()  # noqa: E712
    assert len(live) == 3


@pytest.mark.asyncio
async def test_apply_soft_deletes_dupes_keeps_keeper_and_uniques(db_session, admin_user):
    await _seed(db_session)
    result = await db_cleanup.apply(db_session, admin_user)
    assert result["removed"]["total"] == 3
    # properties: P2 (keeper) + P3 (unique) remain; P1 soft-deleted
    props = {p.id: p.is_deleted for p in (await db_session.execute(select(MortgagedProperty))).scalars().all()}
    assert props["P2"] is False and props["P3"] is False and props["P1"] is True
    # guarantors: G2 keeper + G3 unique remain; G1 removed
    guars = {g.id: g.is_deleted for g in (await db_session.execute(select(Guarantor))).scalars().all()}
    assert guars["G2"] is False and guars["G3"] is False and guars["G1"] is True
    # partners: PT2 keeper remains; PT1 removed
    parts = {p.id: p.is_deleted for p in (await db_session.execute(select(Partner))).scalars().all()}
    assert parts["PT2"] is False and parts["PT1"] is True
    # every removal is logged under the customer's account (shows in the Logs tab)
    logs = (await db_session.execute(select(AuditLog).where(AuditLog.account_no == "500100", AuditLog.action == "delete"))).scalars().all()
    assert len(logs) == 3


@pytest.mark.asyncio
async def test_apply_is_idempotent(db_session, admin_user):
    await _seed(db_session)
    await db_cleanup.apply(db_session, admin_user)
    again = await db_cleanup.apply(db_session, admin_user)
    assert again["removed"]["total"] == 0   # nothing left to remove


@pytest.mark.asyncio
async def test_scan_apply_via_admin_api(client, admin_headers, db_session):
    await _seed(db_session)
    r = await client.post("/api/cleanup/scan", headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.json()["counts"]["total_removals"] == 3
    r2 = await client.post("/api/cleanup/apply", headers=admin_headers, json={})
    assert r2.status_code == 200, r2.text
    assert r2.json()["removed"]["total"] == 3
    # history records the runs
    h = await client.get("/api/cleanup/history", headers=admin_headers)
    assert h.status_code == 200
    kinds = [run["kind"] for run in h.json()["runs"]]
    assert "scan" in kinds and "apply" in kinds


@pytest.mark.asyncio
async def test_cleanup_requires_admin(client, auth_headers):
    r = await client.post("/api/cleanup/scan", headers=auth_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_ai_review_gracefully_unavailable(client, admin_headers, db_session):
    """With no AI model configured, the second-opinion endpoint returns cleanly."""
    await _seed(db_session)
    r = await client.post("/api/cleanup/ai-review", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["available"] is False


# ---- scheduler (review-first; never auto-deletes) ----
def test_schedule_due_logic():
    now = datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)
    # 'off' / unknown → never due
    assert db_cleanup._schedule_due("off", "", now) is False
    assert db_cleanup._schedule_due("", "", now) is False
    # never run before → due now for any real schedule
    assert db_cleanup._schedule_due("daily", "", now) is True
    assert db_cleanup._schedule_due("weekly", "", now) is True
    # ran recently → not due
    recent = (now - timedelta(hours=2)).isoformat()
    assert db_cleanup._schedule_due("daily", recent, now) is False
    # ran long ago → due
    old = (now - timedelta(days=2)).isoformat()
    assert db_cleanup._schedule_due("daily", old, now) is True
    # weekly: 2 days is not enough, 8 days is
    assert db_cleanup._schedule_due("weekly", old, now) is False
    assert db_cleanup._schedule_due("weekly", (now - timedelta(days=8)).isoformat(), now) is True
    # naive timestamp is treated as UTC (no crash)
    assert db_cleanup._schedule_due("daily", "2026-06-01T00:00:00", now) is True


@pytest.mark.asyncio
async def test_scheduled_run_off_does_nothing(db_session):
    await _seed(db_session)
    db_session.add(SystemSetting(key="cleanup_schedule", value="off"))
    await db_session.commit()
    assert await db_cleanup.run_once_scheduled(db_session) is None
    # no run recorded, still 3 live properties (nothing deleted)
    runs = (await db_session.execute(select(CleanupRun))).scalars().all()
    assert runs == []
    live = (await db_session.execute(select(MortgagedProperty).where(MortgagedProperty.is_deleted == False))).scalars().all()  # noqa: E712
    assert len(live) == 3


@pytest.mark.asyncio
async def test_scheduled_run_reviews_but_never_deletes(db_session, admin_user):
    acc = await _seed(db_session)
    db_session.add(SystemSetting(key="cleanup_schedule", value="daily"))
    await db_session.commit()

    report = await db_cleanup.run_once_scheduled(db_session)
    assert report is not None
    assert report["counts"]["total_removals"] == 3

    # a scheduled run is recorded…
    runs = (await db_session.execute(select(CleanupRun).where(CleanupRun.kind == "scheduled"))).scalars().all()
    assert len(runs) == 1 and runs[0].trigger == "schedule"
    # …last_run stamped so it won't immediately re-fire…
    last = (await db_session.execute(select(SystemSetting).where(SystemSetting.key == "cleanup_last_run"))).scalar_one()
    assert last.value
    assert await db_cleanup.run_once_scheduled(db_session) is None  # not due again
    # …admins were notified…
    notes = (await db_session.execute(select(Notification).where(Notification.category == "system"))).scalars().all()
    assert notes and any(n.link == "/cleanup" for n in notes)
    # …but NOTHING was deleted (review-first).
    live = (await db_session.execute(select(MortgagedProperty).where(MortgagedProperty.is_deleted == False))).scalars().all()  # noqa: E712
    assert len(live) == 3
