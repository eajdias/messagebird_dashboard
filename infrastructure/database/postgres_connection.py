import os

import asyncpg


class PostgresPool:
    def __init__(self, dsn: str | None = None, min_size: int = 2, max_size: int = 10):
        self._dsn = dsn or os.getenv(
            "DATABASE_URL",
            "postgresql://mbird:mbird_dev_2024@localhost:5432/mbird_reports",
        )
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    async def start(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
            )

    async def stop(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Pool not started. Call start() first.")
        return self._pool

    async def fetch_all(self, query: str, *params) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *params)

    async def fetch_one(self, query: str, *params) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *params)

    async def fetch_val(self, query: str, *params):
        row = await self.fetch_one(query, *params)
        return row[0] if row else None

    async def execute(self, query: str, *params) -> str:
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *params)
            return result or ""

    async def executemany(self, query: str, params_list: list[tuple]):
        async with self.pool.acquire() as conn:
            await conn.executemany(query, params_list)
