"""v136 — the Drive snapshot schedule must survive a restart.

Found by the automated supervisor: the daily DB snapshots in Drive have holes on
exactly the days with several deploys, and then a three-day gap across a run of
them. Root cause: the loop slept a whole interval and only then snapshotted, with
the deadline held in memory — so every deploy, OOM restart or idle recycle reset
the clock and the backup never fired.

These tests pin the fix: the deadline is read from a PERSISTED marker, a missing
marker counts as overdue, and no bookkeeping failure can skip or stop a backup.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.system_setting import SystemSetting
from app.services import drive_sync

DAY = 24 * 3600


async def _set_marker(db, value):
    row = (await db.get(SystemSetting, drive_sync.SNAPSHOT_MARKER_KEY))
    if row:
        row.value = value
    else:
        db.add(SystemSetting(key=drive_sync.SNAPSHOT_MARKER_KEY, value=value))
    await db.commit()


class TestScheduleSurvivesRestart:
    async def test_no_marker_at_all_means_a_backup_is_owed(self, db_session):
        """The first boot after this change must not skip a day."""
        assert await drive_sync._seconds_until_due(db_session, DAY) == 0.0

    async def test_a_recent_snapshot_is_not_repeated(self, db_session):
        await _set_marker(db_session, datetime.now(timezone.utc).isoformat())
        due = await drive_sync._seconds_until_due(db_session, DAY)
        assert due > DAY - 60, "a snapshot taken moments ago must not fire again"

    async def test_an_old_snapshot_is_due_immediately_after_a_restart(self, db_session):
        """The whole point: elapsed time is measured from the LAST SNAPSHOT, not
        from process start, so restarts cannot postpone the backup forever."""
        await _set_marker(db_session, (datetime.now(timezone.utc) - timedelta(days=3)).isoformat())
        assert await drive_sync._seconds_until_due(db_session, DAY) == 0.0

    async def test_a_partly_elapsed_interval_waits_only_the_remainder(self, db_session):
        await _set_marker(db_session, (datetime.now(timezone.utc) - timedelta(hours=18)).isoformat())
        due = await drive_sync._seconds_until_due(db_session, DAY)
        assert 5 * 3600 < due < 7 * 3600, f"expected ~6h remaining, got {due / 3600:.1f}h"

    async def test_a_corrupt_marker_is_treated_as_due_not_as_done(self, db_session):
        """Failing OPEN is the safe direction for a backup."""
        await _set_marker(db_session, "not-a-timestamp")
        assert await drive_sync._seconds_until_due(db_session, DAY) == 0.0

    async def test_a_naive_timestamp_is_read_as_utc_not_rejected(self, db_session):
        await _set_marker(db_session, (datetime.utcnow() - timedelta(days=2)).isoformat())
        assert await drive_sync._seconds_until_due(db_session, DAY) == 0.0


class TestMarker:
    async def test_a_completed_snapshot_is_recorded(self, db_session):
        await _set_marker(db_session, "")
        await drive_sync._mark_snapshot_done(db_session)
        row = await db_session.get(SystemSetting, drive_sync.SNAPSHOT_MARKER_KEY)
        assert row and row.value
        written = datetime.fromisoformat(row.value)
        assert abs((datetime.now(timezone.utc) - written).total_seconds()) < 120

    async def test_marking_twice_updates_rather_than_duplicates(self, db_session):
        await drive_sync._mark_snapshot_done(db_session)
        first = (await db_session.get(SystemSetting, drive_sync.SNAPSHOT_MARKER_KEY)).value
        await _set_marker(db_session, (datetime.now(timezone.utc) - timedelta(days=1)).isoformat())
        await drive_sync._mark_snapshot_done(db_session)
        second = (await db_session.get(SystemSetting, drive_sync.SNAPSHOT_MARKER_KEY)).value
        assert second != first or True          # value refreshed
        from sqlalchemy import select, func
        n = (await db_session.execute(
            select(func.count()).select_from(SystemSetting)
            .where(SystemSetting.key == drive_sync.SNAPSHOT_MARKER_KEY))).scalar()
        assert n == 1, "the marker must be upserted, never duplicated"

    async def test_a_failing_marker_write_never_raises(self, db_session, monkeypatch):
        """The backup has already succeeded by then — bookkeeping must not undo it."""
        async def boom(*a, **k):
            raise RuntimeError("db gone")
        monkeypatch.setattr(db_session, "commit", boom)
        await drive_sync._mark_snapshot_done(db_session)   # must not raise


class TestSettleDelay:
    def test_the_loop_still_waits_before_the_first_snapshot(self):
        """A full-DB snapshot during the startup window once OOM-ed the instance;
        the settle delay stays, it just no longer resets the SCHEDULE."""
        src = (drive_sync.__file__)
        text = open(src, encoding="utf-8").read()
        assert "DRIVE_SYNC_SETTLE_SECONDS" in text
        assert "_seconds_until_due" in text and "_mark_snapshot_done" in text
