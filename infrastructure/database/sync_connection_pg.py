from contextlib import asynccontextmanager

import asyncpg


class PostgresSyncConnection:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool
        self._conn: asyncpg.Connection | None = None
        self._in_transaction = False

    @asynccontextmanager
    async def transaction(self):
        async with self._pool.acquire() as conn:
            self._conn = conn
            self._in_transaction = True
            try:
                async with conn.transaction():
                    yield self
            finally:
                self._conn = None
                self._in_transaction = False

    async def execute_query(self, query: str, params=()):
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *params)

    async def execute_raw(self, query: str):
        """Execute raw SQL — no prepared statements, no parameter type issues."""
        async with self._pool.acquire() as conn:
            return await conn.execute(query)

    async def execute_many(self, query: str, params_list: list[tuple]):
        if not params_list:
            return
        if self._in_transaction and self._conn:
            await self._conn.executemany(query, params_list)
        else:
            async with self._pool.acquire() as conn:
                await conn.executemany(query, params_list)

    async def fetch_one(self, query: str, params=()):
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *params)

    async def fetch_all(self, query: str, params=()):
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *params)
