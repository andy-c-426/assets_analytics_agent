"""TTL in-memory cache for tool results and derived analytics.

Caches enriched yfinance data per-symbol to avoid redundant API calls and
re-computation during brief analysis sessions.
"""

import time
import threading


class CacheEntry:
    def __init__(self, data: dict, ttl: int):
        self.data = data
        self.expires_at = time.monotonic() + ttl

    @property
    def expired(self) -> bool:
        return time.monotonic() > self.expires_at


class AnalyticsCache:
    """Thread-safe TTL cache for enriched analytics data."""

    def __init__(self):
        self._lock = threading.Lock()
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> dict | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expired:
                del self._store[key]
                return None
            return entry.data

    def set(self, key: str, data: dict, ttl: int = 300):
        with self._lock:
            self._store[key] = CacheEntry(data, ttl)

    def clear(self):
        with self._lock:
            self._store.clear()


# Module-level singleton
_cache = AnalyticsCache()


def get_cache() -> AnalyticsCache:
    return _cache
