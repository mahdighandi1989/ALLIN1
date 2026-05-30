"""In-memory (Redis-aware) login rate limiting and brute-force protection.

This module is the authoritative source of truth for the two anti-brute-force
behaviours required by the auth pipeline:

* **Rate limiting** — after ``LOGIN_RATE_LIMIT_PER_MINUTE`` failed attempts
  within a rolling 60-second window, further attempts for the same key are
  rejected with HTTP ``429 Too Many Requests``.
* **Account lockout** — after ``ACCOUNT_LOCKOUT_THRESHOLD`` failed attempts the
  key is locked for ``ACCOUNT_LOCKOUT_MINUTES`` minutes and every attempt is
  rejected with HTTP ``423 Locked``.

The default backend is a process-local, thread-safe store so the protection
works out of the box (and in tests) without any external dependency. When a
Redis URL is configured the auth router *additionally* mirrors every attempt
into Redis for cross-process accounting/auditing — see
``app.routers.auth._log_login_attempt_to_redis`` — but the decision logic here
remains correct even when Redis is unavailable.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from app.config import settings


class RateLimitStatus(str, Enum):
    """Outcome of a rate-limit / lockout check."""

    OK = "ok"
    RATE_LIMITED = "rate_limited"  # -> HTTP 429
    LOCKED = "locked"  # -> HTTP 423


@dataclass
class _AttemptRecord:
    """Per-key bookkeeping of failed attempts and lockout state."""

    timestamps: List[float] = field(default_factory=list)
    locked_until: float = 0.0


class LoginRateLimiter:
    """Thread-safe sliding-window rate limiter with account lockout.

    All thresholds are read from application settings so they can be tuned via
    environment variables without code changes.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: Dict[str, _AttemptRecord] = {}

    # -- configuration helpers ------------------------------------------------
    @property
    def per_minute_limit(self) -> int:
        return int(getattr(settings, "LOGIN_RATE_LIMIT_PER_MINUTE", 5))

    @property
    def lockout_threshold(self) -> int:
        return int(getattr(settings, "ACCOUNT_LOCKOUT_THRESHOLD", 10))

    @property
    def lockout_seconds(self) -> int:
        return int(getattr(settings, "ACCOUNT_LOCKOUT_MINUTES", 30)) * 60

    # -- internal helpers -----------------------------------------------------
    def _prune(self, record: _AttemptRecord, now: float) -> None:
        """Drop attempts that are older than the (longer) lockout window."""
        horizon = now - self.lockout_seconds
        record.timestamps = [t for t in record.timestamps if t >= horizon]

    def _recent_failures(self, record: _AttemptRecord, now: float) -> int:
        window_start = now - 60.0
        return sum(1 for t in record.timestamps if t >= window_start)

    # -- public API -----------------------------------------------------------
    def check(self, key: str) -> RateLimitStatus:
        """Return whether ``key`` may attempt a login right now.

        A rate-limited attempt is still *recorded* so that a client which keeps
        hammering a throttled account eventually trips the lockout threshold
        instead of being able to retry forever at the 429 boundary.
        """
        now = time.monotonic()
        with self._lock:
            record = self._records.setdefault(key, _AttemptRecord())

            # Active lockout always wins.
            if record.locked_until and now < record.locked_until:
                return RateLimitStatus.LOCKED

            self._prune(record, now)

            # Too many total failures within the lockout window -> lock it.
            if len(record.timestamps) >= self.lockout_threshold:
                record.locked_until = now + self.lockout_seconds
                return RateLimitStatus.LOCKED

            # Too many failures in the last minute -> throttle (and count it).
            if self._recent_failures(record, now) >= self.per_minute_limit:
                record.timestamps.append(now)
                if len(record.timestamps) >= self.lockout_threshold:
                    record.locked_until = now + self.lockout_seconds
                    return RateLimitStatus.LOCKED
                return RateLimitStatus.RATE_LIMITED

            return RateLimitStatus.OK

    def register_failure(self, key: str) -> None:
        """Record a failed authentication for ``key``."""
        now = time.monotonic()
        with self._lock:
            record = self._records.setdefault(key, _AttemptRecord())
            self._prune(record, now)
            record.timestamps.append(now)
            if len(record.timestamps) >= self.lockout_threshold:
                record.locked_until = now + self.lockout_seconds

    def reset(self, key: str) -> None:
        """Clear all failure state for ``key`` (e.g. after a successful login)."""
        with self._lock:
            self._records.pop(key, None)

    def reset_all(self) -> None:
        """Clear the entire store — primarily for test isolation."""
        with self._lock:
            self._records.clear()


# Process-wide singleton used by the auth router.
login_rate_limiter = LoginRateLimiter()


def reset_all() -> None:
    """Module-level convenience used by test fixtures."""
    login_rate_limiter.reset_all()
