"""In-memory async cache with TTL for repository queries."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger("m_bird.cache")


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL expiration and LRU eviction.

    Uses asyncio locks for thread safety. Per-key locks prevent thundering herd
    — only one coroutine computes each cache key at a time.

    Usage:
        cache = TTLCache(default_ttl=300)  # 5 min default
        result = await cache.get_or_set("key", async_factory)
        cache.invalidate("key")
        cache.clear()
    """

    def __init__(self, default_ttl: int = 300, maxsize: int = 1000):
        self._default_ttl = default_ttl
        self._maxsize = maxsize
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._key_locks: dict[str, asyncio.Lock] = {}

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: int | None = None,
    ) -> Any:
        """Return cached value or call factory, cache, and return.

        ``factory`` may be a coroutine function or a plain callable.
        Uses per-key locks to prevent thundering herd on cache miss.
        """
        now = time.monotonic()
        effective_ttl = ttl if ttl is not None else self._default_ttl

        async with self._lock:
            if key in self._store:
                expires, value = self._store[key]
                if now < expires:
                    logger.debug("cache HIT: %s", key)
                    return value
                del self._store[key]
            # Get or create per-key lock
            if key not in self._key_locks:
                self._key_locks[key] = asyncio.Lock()
            key_lock = self._key_locks[key]

        async with key_lock:
            # Double-check: another coroutine may have populated while we waited
            async with self._lock:
                if key in self._store:
                    expires, value = self._store[key]
                    if now < expires:
                        logger.debug("cache HIT (after wait): %s", key)
                        return value
                    del self._store[key]

            logger.debug("cache MISS: %s", key)
            if inspect.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()

            async with self._lock:
                self._store[key] = (now + effective_ttl, value)

            return value

    async def get(self, key: str) -> Any | None:
        """Return cached value if present and not expired, else None."""
        now = time.monotonic()
        async with self._lock:
            if key in self._store:
                expires, value = self._store[key]
                if now < expires:
                    logger.debug("cache GET hit: %s", key)
                    return value
                del self._store[key]
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache with LRU eviction when maxsize is reached."""
        now = time.monotonic()
        effective_ttl = ttl if ttl is not None else self._default_ttl
        async with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (now + effective_ttl, value)
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def invalidate_prefix(self, prefix: str) -> int:
        """Remove all keys starting with *prefix*. Returns count removed."""
        async with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._store[k]
            return len(keys_to_remove)


# Module-level singleton
repo_cache = TTLCache(default_ttl=300, maxsize=1000)

# Cache for processed (aggregated) results — avoids re-running aggregator pipeline
processed_cache = TTLCache(default_ttl=300, maxsize=500)
