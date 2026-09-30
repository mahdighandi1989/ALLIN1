"""v168 — WHEN DOES THE SUPERVISOR COME? Answered from evidence, not from faith.

«وقتی دکمه فوری میزنم باید ناظر بگه چند دقیقه دیگه میره سراغش … هر دور دقیق به
ساعت محلی بسنجه و پیام بده» — the owner, 2026-09-30.

THE PROBLEM WITH THE OBVIOUS ANSWER
-----------------------------------
The urgent round is a scheduled Routine living in claude.ai, not in this repo.
The backend cannot read that schedule, so writing «hourly at :23» into the code
would be a number that is true only until someone edits the Routine — and a
countdown that is quietly wrong is worse than no countdown, because the owner
plans around it.

So the schedule is MEASURED. The round already knocks on this server every time
it runs (it claims the fast queue even when the queue is empty), which makes it
a heartbeat. From the last few knocks we can say when the next one is due, and
say so honestly:

    observed  — we have watched it and this is when it is next due
    assumed   — nothing watched yet; this is the configured default
    stale     — it has not knocked for several cycles; the Routine may be off

`stale` exists because «unmeasured» and «zero» must never look the same
(`experiences/a-monitor-must-distinguish-unmeasured-from-zero.md`). A silent
supervisor should read as «something is wrong», not as «about an hour».

Pure on purpose: it takes a clock and a list of timestamps and returns the
answer, so the whole thing is testable without a scheduler, a DB or a network.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

#: How many knocks we keep. Enough to see the cadence through one missed run,
#: small enough that a `system_settings` row stays a row and not a log file.
KEEP = 12

#: The minute past the hour the urgent Routine is configured for, used only
#: until the first knocks have been recorded. It has to match the Routine; when
#: they disagree, the OBSERVED value wins within one round, which is the point.
ASSUMED_MINUTE = 23

#: Anything outside this is not «hourly», so the cadence is taken as measured
#: rather than snapped to the top of the hour.
HOURLY_LO, HOURLY_HI = 45 * 60, 75 * 60

#: Missing this many cycles in a row means the Routine is probably not running.
STALE_CYCLES = 3


def record_round(raw: str | None, now: datetime, keep: int = KEEP) -> str:
    """Add this knock to the log, newest last, capped at `keep`."""
    stamps = _parse(raw)
    stamps.append(_utc(now))
    stamps = sorted(set(stamps))[-keep:]
    return json.dumps([s.isoformat() for s in stamps])


def next_round(now: datetime,
               raw: str | None,
               assumed_minute: int = ASSUMED_MINUTE) -> dict:
    """When the fast queue is next picked up, and how sure we are.

    Returns ``{at, in_seconds, in_minutes, every_minutes, basis, last_seen}``
    with ``at`` an ISO-8601 UTC instant. The caller renders it in ITS OWN local
    time — the server never guesses the reader's timezone, because a number that
    says «۱۹ دقیقهٔ دیگر» has to be right on the reader's own clock.
    """
    now = _utc(now)
    stamps = _parse(raw)
    gaps = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])
            if 0 < (b - a).total_seconds() <= 24 * 3600]

    basis, every = "assumed", 3600.0
    at = _at_minute(now, assumed_minute)

    if gaps:
        every = _median(gaps)
        if HOURLY_LO <= every <= HOURLY_HI:
            # An hourly round: the minute it lands on is the stable fact, so a
            # single late run does not drag the estimate around.
            at = _at_minute(now, _common_minute(stamps))
            every = 3600.0
        else:
            # Some other cadence — step forward from the last knock.
            at = stamps[-1]
            while at <= now:
                at += timedelta(seconds=every)
        basis = "observed"
        if (now - stamps[-1]).total_seconds() > STALE_CYCLES * every:
            basis = "stale"

    return {
        "at": at.isoformat(),
        "in_seconds": max(0, int((at - now).total_seconds())),
        "in_minutes": max(0, int(round((at - now).total_seconds() / 60))),
        "every_minutes": int(round(every / 60)),
        "basis": basis,
        "last_seen": stamps[-1].isoformat() if stamps else None,
    }


# --------------------------------------------------------------------------- #

def _parse(raw: str | None) -> list[datetime]:
    try:
        vals = json.loads(raw) if raw else []
    except (ValueError, TypeError):
        return []                      # a corrupted row must not break the page
    out = []
    for v in vals if isinstance(vals, list) else []:
        try:
            out.append(_utc(datetime.fromisoformat(str(v))))
        except (ValueError, TypeError):
            continue
    return sorted(out)


def _utc(d: datetime) -> datetime:
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _common_minute(stamps: list[datetime]) -> int:
    """The minute past the hour it usually lands on — the mode, newest winning
    a tie, so a schedule that was changed is followed rather than averaged."""
    counts: dict[int, int] = {}
    for s in stamps:
        counts[s.minute] = counts.get(s.minute, 0) + 1
    best = max(counts.values())
    for s in reversed(stamps):
        if counts[s.minute] == best:
            return s.minute
    return stamps[-1].minute


def _at_minute(now: datetime, minute: int) -> datetime:
    minute = max(0, min(59, int(minute)))
    at = now.replace(minute=minute, second=0, microsecond=0)
    if at <= now:
        at += timedelta(hours=1)
    return at
