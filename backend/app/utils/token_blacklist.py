"""Token revocation ("blacklist") store for JWT logout / session invalidation.

When a user logs out, the JWT they presented is added to this blacklist keyed by
its ``jti`` (JWT ID) claim until the token would have naturally expired. Every
authenticated request then checks the blacklist (see
``app.utils.security.verify_access_token``) and rejects any *revoked* token even
though its signature is still cryptographically valid.

The default backend is a thread-safe, process-local store with lazy expiry so
logout works without external infrastructure (and in tests). When a Redis URL is
configured the store transparently mirrors revocations into Redis so the
blacklist is shared across worker processes/instances.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class TokenBlacklist:
    """Thread-safe store of revoked JWT ``jti`` values with TTL-based expiry."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # jti -> unix timestamp after which the entry can be forgotten.
        self._revoked: Dict[str, float] = {}
        self._redis = None
        self._redis_attempted = False

    # -- optional Redis backend ----------------------------------------------
    def _get_redis(self):
        """Lazily build a Redis client when REDIS_URL is configured.

        Failures are swallowed: the in-memory store remains authoritative so a
        missing/broken Redis never breaks logout.
        """
        if self._redis_attempted:
            return self._redis
        self._redis_attempted = True
        redis_url = getattr(settings, "REDIS_URL", None)
        if not redis_url:
            return None
        try:  # pragma: no cover - exercised only when Redis is installed
            import redis  # type: ignore

            self._redis = redis.Redis.from_url(redis_url)
        except Exception as exc:  # pragma: no cover
            logger.warning("Token blacklist Redis backend unavailable: %s", exc)
            self._redis = None
        return self._redis

    # -- internal helpers -----------------------------------------------------
    def _purge_expired(self, now: float) -> None:
        expired = [jti for jti, exp in self._revoked.items() if exp <= now]
        for jti in expired:
            self._revoked.pop(jti, None)

    # -- public API -----------------------------------------------------------
    def revoke(self, jti: str, expires_at: Optional[float] = None) -> None:
        """Add ``jti`` to the blacklist until ``expires_at`` (unix seconds)."""
        if not jti:
            return
        now = time.time()
        # Default TTL mirrors the access-token lifetime.
        ttl_seconds = int(getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)) * 60
        exp = expires_at if expires_at and expires_at > now else now + ttl_seconds
        with self._lock:
            self._purge_expired(now)
            self._revoked[jti] = exp

        redis_client = self._get_redis()
        if redis_client is not None:  # pragma: no cover
            try:
                redis_client.set(
                    f"blacklist:{jti}", "revoked", ex=max(1, int(exp - now))
                )
            except Exception as exc:
                logger.warning("Failed to persist revoked token to Redis: %s", exc)

    def is_revoked(self, jti: str) -> bool:
        """Return ``True`` if ``jti`` has been revoked and not yet expired."""
        if not jti:
            return False
        now = time.time()
        with self._lock:
            exp = self._revoked.get(jti)
            if exp is not None:
                if exp > now:
                    return True
                self._revoked.pop(jti, None)

        redis_client = self._get_redis()
        if redis_client is not None:  # pragma: no cover
            try:
                if redis_client.get(f"blacklist:{jti}") is not None:
                    return True
            except Exception as exc:
                logger.warning("Failed to read revoked token from Redis: %s", exc)
        return False

    def reset_all(self) -> None:
        """Clear the entire blacklist — primarily for test isolation."""
        with self._lock:
            self._revoked.clear()


# Process-wide singleton.
token_blacklist = TokenBlacklist()


def reset_all() -> None:
    """Module-level convenience used by test fixtures."""
    token_blacklist.reset_all()
