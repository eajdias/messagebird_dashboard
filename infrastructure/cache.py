"""In-memory async cache with TTL for repository queries."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger("m_bird.cache")


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL expiration.

    Usage:
        cache = TTLCache(default_ttl=300)  # 5 min default
        result = await cache.get_or_set("key", async_factory)
        cache.invalidate("key")
        cache.clear()
    """

    def __init__(self, default_ttl: int = 300):
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: int | None = None,
    ) -> Any:
        """Return cached value or call factory, cache, and return.

        ``factory`` may be a coroutine function or a plain callable.
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

        # Outside lock: compute value
        logger.debug("cache MISS: %s", key)
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        async with self._lock:
            self._store[key] = (now + effective_ttl, value)

        return value

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
repo_cache = TTLCache(default_ttl=300)
