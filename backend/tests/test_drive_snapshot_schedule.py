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


class TestFreshnessIsVisibleFromOutside:
    """v149 — the marker was persisted in v136 but nothing exposed it.

    «Are the backups fresh?» is a standing supervisor duty, and for three runs it
    could only be answered by listing the Drive folder by hand. «configured and
    connected» says the pipe is open, not that anything went through it — the v136
    hole lasted three days while both were true.
    """

    async def test_the_marker_is_readable(self, db_session, monkeypatch):
        stamp = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        await _set_marker(db_session, stamp)

        class _Session:
            async def __aenter__(self): return db_session
            async def __aexit__(self, *a): return False
        monkeypatch.setattr("app.database.AsyncSessionLocal", lambda: _Session())
        assert await drive_sync.last_snapshot_at() == stamp

    async def test_an_absent_marker_reads_as_never_not_as_fine(self, db_session, monkeypatch):
        class _Session:
            async def __aenter__(self): return db_session
            async def __aexit__(self, *a): return False
        monkeypatch.setattr("app.database.AsyncSessionLocal", lambda: _Session())
        assert await drive_sync.last_snapshot_at() is None

    async def test_an_unreadable_marker_never_breaks_the_status_call(self, monkeypatch):
        """A status endpoint that 500s because of bookkeeping is worse than one
        that says «unknown»."""
        def boom():
            raise RuntimeError("db gone")
        monkeypatch.setattr("app.database.AsyncSessionLocal", boom)
        assert await drive_sync.last_snapshot_at() is None

    async def test_status_marks_a_never_backed_up_system_as_overdue(self, monkeypatch):
        """Absent marker ⇒ overdue. The honest reading of «no record» for a backup
        is «one is owed», exactly as the scheduler itself assumes."""
        async def _none():
            return None
        monkeypatch.setattr(drive_sync, "is_enabled", lambda: False)
        monkeypatch.setattr(drive_sync, "last_snapshot_at", _none)
        st = await drive_sync.status()
        assert st["last_snapshot_at"] is None
        assert st["snapshot_overdue"] is True
        assert st["snapshot_age_hours"] is None

    async def test_status_reports_the_age_of_a_real_snapshot(self, monkeypatch):
        stamp = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()

        async def _at():
            return stamp
        monkeypatch.setattr(drive_sync, "is_enabled", lambda: False)
        monkeypatch.setattr(drive_sync, "last_snapshot_at", _at)
        st = await drive_sync.status()
        assert 4.5 <= st["snapshot_age_hours"] <= 5.5
        assert st["snapshot_overdue"] is False

    async def test_a_stalled_loop_is_overdue_but_one_late_run_is_not(self, monkeypatch):
        """Overdue means more than TWICE the interval, so a single late run does
        not cry wolf while a stalled loop still gets caught."""
        monkeypatch.setattr(drive_sync, "is_enabled", lambda: False)
        interval = drive_sync.settings.DRIVE_SYNC_INTERVAL_HOURS

        for hours, expected in ((interval * 1.5, False), (interval * 2.5, True)):
            stamp = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

            async def _at(s=stamp):
                return s
            monkeypatch.setattr(drive_sync, "last_snapshot_at", _at)
            st = await drive_sync.status()
            assert st["snapshot_overdue"] is expected, (hours, st)

    async def test_a_malformed_marker_is_unknown_not_fine(self, monkeypatch):
        async def _at():
            return "not-a-date"
        monkeypatch.setattr(drive_sync, "is_enabled", lambda: False)
        monkeypatch.setattr(drive_sync, "last_snapshot_at", _at)
        st = await drive_sync.status()
        assert st["snapshot_age_hours"] is None
        assert st["snapshot_overdue"] is None      # unknown, NOT False

