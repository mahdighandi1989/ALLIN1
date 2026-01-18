"""
Simple in-memory cache for frequently accessed data
کش ساده برای داده‌های پرکاربرد
"""
from typing import Any, Optional
from datetime import datetime, timedelta
from functools import wraps
import asyncio


class SimpleCache:
    """Thread-safe simple in-memory cache with TTL"""

    def __init__(self):
        self._cache: dict = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if expires_at > datetime.utcnow():
                    return value
                else:
                    # Remove expired entry
                    del self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 60):
        """Set value in cache with TTL"""
        async with self._lock:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expires_at)

    async def delete(self, key: str):
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]

    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self):
        """Remove all expired entries"""
        async with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, (_, expires_at) in self._cache.items()
                if expires_at <= now
            ]
            for key in expired_keys:
                del self._cache[key]


# Global cache instance
cache = SimpleCache()


def cached(ttl_seconds: int = 60, key_prefix: str = ""):
    """
    Decorator to cache async function results

    Usage:
        @cached(ttl_seconds=300, key_prefix="ai_status")
        async def get_ai_status():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{hash(args)}"
            if kwargs:
                cache_key += f":{hash(frozenset(kwargs.items()))}"

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper
    return decorator
