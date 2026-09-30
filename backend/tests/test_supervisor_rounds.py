"""v168 — «چند دقیقهٔ دیگر می‌رود سراغش؟» has to be right on the owner's clock.

The estimate is MEASURED from the round's own knocks rather than hard-coded,
because the schedule lives in a Routine this server cannot read. These tests are
all pure: a clock, a list of timestamps, and the answer.
"""
import json
from datetime import datetime, timedelta, timezone

from app.services.supervisor_rounds import (
    ASSUMED_MINUTE, next_round, record_round,
)

UTC = timezone.utc


def at(h, m, day=30):
    return datetime(2026, 9, day, h, m, tzinfo=UTC)


def log(*stamps):
    return json.dumps([s.isoformat() for s in stamps])


class TestWithNothingObservedYet:
    def test_it_falls_back_to_the_configured_minute_and_says_so(self):
        r = next_round(at(10, 4), None)
        assert r["basis"] == "assumed"
        assert r["at"] == at(10, ASSUMED_MINUTE).isoformat()
        assert r["in_minutes"] == 19

    def test_past_that_minute_it_means_the_NEXT_hour(self):
        r = next_round(at(10, 40), None)
        assert r["at"] == at(11, ASSUMED_MINUTE).isoformat()
        assert r["in_minutes"] == 43

    def test_exactly_on_the_minute_is_the_next_hour_not_right_now(self):
        """«0 minutes» would read as «it is happening», and the owner would
        watch a queue that nothing is touching for an hour."""
        r = next_round(at(10, ASSUMED_MINUTE), None)
        assert r["at"] == at(11, ASSUMED_MINUTE).isoformat()

    def test_a_corrupted_log_does_not_break_the_answer(self):
        for bad in ("not json", "{}", '["nonsense"]', "[123]"):
            assert next_round(at(10, 4), bad)["basis"] == "assumed"


class TestOnceItHasBeenWatched:
    def test_it_follows_what_the_round_ACTUALLY_does(self):
        """The Routine was moved to :07. Nothing here was edited, and the
        estimate follows within one round — which is the whole reason it is
        measured instead of written down."""
        r = next_round(at(10, 30), log(at(8, 7), at(9, 7), at(10, 7)))
        assert r["basis"] == "observed"
        assert r["at"] == at(11, 7).isoformat()
        assert r["every_minutes"] == 60

    def test_one_late_run_does_not_drag_the_estimate(self):
        r = next_round(at(10, 30), log(at(8, 7), at(9, 7), at(10, 9)))
        assert r["at"] == at(11, 7).isoformat()      # the usual minute, not 09

    def test_a_schedule_that_changed_wins_the_tie(self):
        """Two knocks at :07 and two at :40 — the newer pair is what it does
        now, so an averaged answer would be wrong for both."""
        r = next_round(at(12, 50), log(at(8, 7), at(9, 7), at(11, 40), at(12, 40)))
        assert r["at"] == at(13, 40).isoformat()

    def test_a_non_hourly_cadence_is_measured_not_snapped(self):
        r = next_round(at(13, 0), log(at(6, 15), at(9, 15), at(12, 15)))
        assert r["every_minutes"] == 180
        assert r["at"] == at(15, 15).isoformat()

    def test_a_single_knock_is_not_yet_a_cadence(self):
        assert next_round(at(10, 30), log(at(9, 7)))["basis"] == "assumed"


class TestWhenTheRoutineStops:
    def test_a_long_silence_reads_as_stale_not_as_about_an_hour(self):
        """«unmeasured» and «zero» must not look the same. A Routine that was
        switched off would otherwise keep promising «۱۹ دقیقهٔ دیگر» forever."""
        r = next_round(at(18, 0), log(at(8, 7), at(9, 7), at(10, 7)))
        assert r["basis"] == "stale"
        assert r["last_seen"] == at(10, 7).isoformat()

    def test_one_missed_round_is_not_stale(self):
        r = next_round(at(11, 30), log(at(8, 7), at(9, 7), at(10, 7)))
        assert r["basis"] == "observed"


class TestTheLog:
    def test_it_keeps_the_newest_and_drops_the_rest(self):
        raw = None
        for h in range(20):
            raw = record_round(raw, at(h % 24, 7, day=1 + h // 24), keep=5)
        kept = json.loads(raw)
        assert len(kept) == 5
        assert kept == sorted(kept)

    def test_the_same_instant_twice_is_recorded_once(self):
        raw = record_round(record_round(None, at(9, 7)), at(9, 7))
        assert len(json.loads(raw)) == 1

    def test_a_naive_timestamp_is_read_as_utc_not_rejected(self):
        raw = record_round(None, datetime(2026, 9, 30, 9, 7))
        assert json.loads(raw) == [at(9, 7).isoformat()]

    def test_a_knock_out_of_order_still_lands_in_order(self):
        raw = record_round(record_round(None, at(10, 7)), at(9, 7))
        assert json.loads(raw) == [at(9, 7).isoformat(), at(10, 7).isoformat()]


class TestTheNumbersTheOwnerReads:
    def test_seconds_and_minutes_agree(self):
        r = next_round(at(10, 4), None)
        assert r["in_seconds"] == 19 * 60
        assert r["in_minutes"] == 19

    def test_it_never_counts_backwards(self):
        r = next_round(at(10, 22, day=30) + timedelta(seconds=59), None)
        assert r["in_seconds"] >= 0 and r["in_minutes"] >= 0
