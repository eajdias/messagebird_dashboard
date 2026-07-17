import asyncio
from contextlib import asynccontextmanager

import aiosqlite


class SyncConnection:
    """Persistent connection for bulk sync operations."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = None
        self._in_transaction = False
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        self.db = await aiosqlite.connect(self.db_path, isolation_level=None)
        self.db.row_factory = aiosqlite.Row

        async with self._lock:
            await self.db.execute("PRAGMA journal_mode=WAL")
            await self.db.execute("PRAGMA synchronous=NORMAL")
            await self.db.execute("PRAGMA foreign_keys=ON")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            await self.db.close()

    @asynccontextmanager
    async def transaction(self):
        """Context manager for manual transaction blocks."""
        await self._lock.acquire()
        try:
            if not self._in_transaction:
                await self.db.execute("BEGIN")
                self._in_transaction = True

            try:
                yield self
                await self.db.execute("COMMIT")
            except Exception:
                await self.db.execute("ROLLBACK")
                raise
            finally:
                self._in_transaction = False
        finally:
            self._lock.release()

    async def execute_query(self, query, params=()):
        if self._in_transaction:
            async with self.db.execute(query, params) as cursor:
                return await cursor.fetchall()
        async with self._lock, self.db.execute(query, params) as cursor:
            return await cursor.fetchall()

    async def execute_many(self, query, params_list):
        if not params_list:
            return
        if self._in_transaction:
            await self.db.executemany(query, params_list)
            return
        async with self._lock:
            await self.db.executemany(query, params_list)

    async def fetch_one(self, query, params=()):
        if self._in_transaction:
            async with self.db.execute(query, params) as cursor:
                return await cursor.fetchone()
        async with self._lock, self.db.execute(query, params) as cursor:
            return await cursor.fetchone()

    async def fetch_all(self, query, params=()):
        if self._in_transaction:
            async with self.db.execute(query, params) as cursor:
                return await cursor.fetchall()
        async with self._lock, self.db.execute(query, params) as cursor:
            return await cursor.fetchall()
