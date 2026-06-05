"""Unit tests for the login rate-limiter / brute-force protection logic.

These tests exercise ``app.utils.rate_limit.LoginRateLimiter`` directly (no HTTP
layer) so the sliding-window throttling and account-lockout state machine is
verified in isolation from FastAPI. The integration-level behaviour (a real
``POST /api/auth/login`` returning HTTP 429) lives in
``tests/integration/test_auth_rate_limit.py``.
"""
import pytest

from app.config import settings
from app.utils.rate_limit import (
    LoginRateLimiter,
    RateLimitStatus,
    login_rate_limiter,
    reset_all,
)


@pytest.fixture(autouse=True)
def _clean_global_limiter():
    """Keep the process-wide singleton clean around every test."""
    reset_all()
    yield
    reset_all()


def test_rate_limiting_logic():
    """After ``LOGIN_RATE_LIMIT_PER_MINUTE`` failures a key is rate-limited.

    Walks the limiter through its full lifecycle:

    * a fresh key is allowed (``OK``);
    * staying just below the per-minute limit keeps it allowed;
    * crossing the per-minute limit flips it to ``RATE_LIMITED`` (HTTP 429);
    * the limit is read from configuration, not hard-coded;
    * ``reset`` clears the state so a successful login un-throttles the key.
    """
    limiter = LoginRateLimiter()
    key = "user|1.2.3.4"

    per_minute = settings.LOGIN_RATE_LIMIT_PER_MINUTE
    assert per_minute == limiter.per_minute_limit

    # 1) A brand-new key may always attempt a login.
    assert limiter.check(key) == RateLimitStatus.OK

    # 2) Record one fewer than the limit; the key stays OK.
    for _ in range(per_minute - 1):
        limiter.register_failure(key)
    assert limiter.check(key) == RateLimitStatus.OK

    # 3) The failure that reaches the per-minute limit trips the throttle.
    limiter.register_failure(key)
    assert limiter.check(key) == RateLimitStatus.RATE_LIMITED

    # 4) A different key is unaffected — throttling is strictly per-key.
    assert limiter.check("other|9.9.9.9") == RateLimitStatus.OK

    # 5) A successful login resets the key back to OK.
    limiter.reset(key)
    assert limiter.check(key) == RateLimitStatus.OK


def test_account_lockout_after_threshold():
    """Crossing ``ACCOUNT_LOCKOUT_THRESHOLD`` failures locks the key (HTTP 423)."""
    limiter = LoginRateLimiter()
    key = "victim|5.6.7.8"

    for _ in range(limiter.lockout_threshold):
        limiter.register_failure(key)

    assert limiter.check(key) == RateLimitStatus.LOCKED

    # Lockout state is cleared by an explicit reset (e.g. admin unlock / success).
    limiter.reset(key)
    assert limiter.check(key) == RateLimitStatus.OK


def test_reset_all_clears_every_key():
    """``reset_all`` wipes the shared singleton used by the auth router."""
    login_rate_limiter.register_failure("a|ip")
    login_rate_limiter.register_failure("b|ip")
    reset_all()
    assert login_rate_limiter.check("a|ip") == RateLimitStatus.OK
    assert login_rate_limiter.check("b|ip") == RateLimitStatus.OK
