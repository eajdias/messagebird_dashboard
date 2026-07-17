from contextlib import asynccontextmanager

import aiosqlite


class DatabaseConnection:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def fetch_all(self, query: str, params: tuple = ()):
        async with self.get_connection() as db, db.execute(query, params) as cursor:
            return await cursor.fetchall()

    async def fetch_one(self, query: str, params: tuple = ()):
        async with self.get_connection() as db, db.execute(query, params) as cursor:
            return await cursor.fetchone()

    async def fetch_val(self, query: str, params: tuple = ()):
        row = await self.fetch_one(query, params)
        if row:
            return row[0]
        return None
