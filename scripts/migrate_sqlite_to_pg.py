#!/usr/bin/env python3
"""Migrate data from legacy SQLite (m_bird.db) to PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_pg.py --sqlite-path m_bird.db
    python scripts/migrate_sqlite_to_pg.py --sqlite-path /path/to/m_bird.db --pg-dsn postgresql://...

Reads all rows from SQLite contacts, agents, conversations, messages tables
and inserts them into PostgreSQL preserving integer IDs and FK relationships.

The script dynamically detects columns from both databases and only migrates
the intersection, so it handles schema differences gracefully.

The sync and sync_errors tables are skipped (runtime data, will be recreated by pg_sync_engine).
"""

import argparse
import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite
import asyncpg

BATCH_SIZE = 500

# Tables in FK dependency order
TABLE_NAMES = ["contacts", "agents", "conversations", "messages"]

# Columns that are TIMESTAMP in PG and stored as strings in SQLite.
# Any column name matching this pattern will be auto-detected as needing conversion.
TIMESTAMP_SUFFIXES = ("_created", "_updated", "_last")


async def get_sqlite_columns(db: aiosqlite.Connection, table: str) -> list[str]:
    """Get column names from SQLite table via PRAGMA."""
    cursor = await db.execute(f"PRAGMA table_info({table})")
    rows = await cursor.fetchall()
    return [row[1] for row in rows]


async def get_pg_columns(conn: asyncpg.PoolConnectionProxy, table: str) -> list[str]:
    """Get column names from PostgreSQL table via information_schema."""
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name = $1 ORDER BY ordinal_position",
        table,
    )
    return [r["column_name"] for r in rows]


def build_insert_sql(table_name: str, columns: list[str]) -> str:
    """Build an INSERT ... ON CONFLICT DO NOTHING statement for asyncpg."""
    cols = ", ".join(columns)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
    return f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"


def parse_dt(value: Any) -> datetime | None:
    """Parse a datetime string from SQLite into a naive datetime for asyncpg."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError, TypeError:
        return None


def is_timestamp_column(col: str) -> bool:
    """Check if a column name looks like a timestamp column."""
    return any(col.endswith(suffix) for suffix in TIMESTAMP_SUFFIXES)


async def count_rows(sqlite_path: str) -> dict[str, int]:
    """Count all rows in each SQLite table."""
    counts: dict[str, int] = {}
    async with aiosqlite.connect(sqlite_path) as db:
        for name in TABLE_NAMES:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {name}")
            row = await cursor.fetchone()
            counts[name] = row[0] if row else 0
    return counts


async def detect_columns(
    sqlite_path: str,
    pg_pool: asyncpg.Pool,
) -> dict[str, list[str]]:
    """Detect the intersection of columns between SQLite and PG for each table."""
    result: dict[str, list[str]] = {}
    async with aiosqlite.connect(sqlite_path) as sqlite_db, pg_pool.acquire() as pg_conn:
        for name in TABLE_NAMES:
            sqlite_cols = set(await get_sqlite_columns(sqlite_db, name))
            pg_cols = set(await get_pg_columns(pg_conn, name))
            common = sorted(sqlite_cols & pg_cols)
            result[name] = common
            dropped = sorted(sqlite_cols - pg_cols)
            if dropped:
                print(f"  {name}: skipping extra SQLite cols: {', '.join(dropped)}")
    return result


async def migrate_table(
    sqlite_path: str,
    pg_pool: asyncpg.Pool,
    table_name: str,
    columns: list[str],
    dry_run: bool = False,
) -> int:
    """Migrate a single table. Returns row count."""
    insert_sql = build_insert_sql(table_name, columns)
    total = 0

    async with aiosqlite.connect(sqlite_path) as sqlite_db:
        sqlite_db.row_factory = aiosqlite.Row
        cols_sql = ", ".join(columns)
        cursor = await sqlite_db.execute(
            f"SELECT {cols_sql} FROM {table_name} ORDER BY 1",
        )
        batch: list[tuple[object, ...]] = []

        async for row in cursor:
            values = []
            for col in columns:
                val = row[col]  # type: ignore[index]
                if is_timestamp_column(col):
                    val = parse_dt(val)
                values.append(val)
            batch.append(tuple(values))

            if len(batch) >= BATCH_SIZE:
                if not dry_run:
                    async with pg_pool.acquire() as conn:
                        await conn.executemany(insert_sql, batch)
                total += len(batch)
                batch.clear()

        if batch:
            if not dry_run:
                async with pg_pool.acquire() as conn:
                    await conn.executemany(insert_sql, batch)
            total += len(batch)

    return total


async def reset_sequences(pg_pool: asyncpg.Pool) -> None:
    """Reset PostgreSQL SERIAL sequences to max(id)+1 for each table."""
    sequence_map = {
        "contacts": ("contacts", "cnts_id", "contacts_cnts_id_seq"),
        "agents": ("agents", "agnt_id", "agents_agnt_id_seq"),
        "conversations": ("conversations", "cnvs_id", "conversations_cnvs_id_seq"),
        "messages": ("messages", "msgs_id", "messages_msgs_id_seq"),
    }

    async with pg_pool.acquire() as conn:
        for _, (tbl, col, seq) in sequence_map.items():
            row = await conn.fetchrow(f"SELECT COALESCE(MAX({col}), 0) + 1 FROM {tbl}")
            if row:
                next_val = row[0]
                await conn.execute(f"SELECT setval('{seq}', {next_val})")
                print(f"  Sequence {seq} -> {next_val}")


async def verify_migration(
    sqlite_path: str,
    pg_pool: asyncpg.Pool,
    counts: dict[str, int],
) -> bool:
    """Compare row counts between SQLite and PostgreSQL."""
    print("\n-- Verification --")
    all_ok = True

    async with pg_pool.acquire() as pg_conn:
        for name in TABLE_NAMES:
            pg_row = await pg_conn.fetchrow(f"SELECT COUNT(*) FROM {name}")
            pg_count = pg_row[0] if pg_row else 0
            sqlite_count = counts.get(name, 0)
            match = "OK" if sqlite_count == pg_count else "MISMATCH"
            if sqlite_count != pg_count:
                all_ok = False
            print(f"  {name}: SQLite={sqlite_count}  PG={pg_count}  {match}")

    return all_ok


async def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite to PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        default="m_bird.db",
        help="Path to SQLite database file (default: m_bird.db)",
    )
    parser.add_argument(
        "--pg-dsn",
        default=None,
        help="PostgreSQL DSN (default: DATABASE_URL env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count rows without inserting",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip post-migration verification",
    )
    args = parser.parse_args()

    # Resolve SQLite path
    sqlite_path = args.sqlite_path
    if not os.path.isabs(sqlite_path):
        project_root = Path(__file__).resolve().parent.parent
        candidate = project_root / sqlite_path
        if candidate.exists():
            sqlite_path = str(candidate)

    if not os.path.exists(sqlite_path):
        print(f"Error: SQLite file not found: {sqlite_path}")
        sys.exit(1)

    # Resolve PG DSN
    pg_dsn = args.pg_dsn or os.getenv("DATABASE_URL")
    if not pg_dsn and not args.dry_run:
        print("Error: No PostgreSQL DSN. Use --pg-dsn or set DATABASE_URL env var.")
        sys.exit(1)

    # Normalize DSN: asyncpg requires "postgresql://" not "postgresql+asyncpg://"
    if pg_dsn:
        pg_dsn = pg_dsn.replace("postgresql+asyncpg://", "postgresql://")
        pg_dsn = pg_dsn.replace("postgres+asyncpg://", "postgresql://")

    print(f"SQLite: {sqlite_path}")
    if pg_dsn:
        print(f"PostgreSQL: {pg_dsn.split('@')[-1] if '@' in pg_dsn else pg_dsn}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'MIGRATE'}")
    print()

    # Count source rows
    counts = await count_rows(sqlite_path)
    total_source = sum(counts.values())
    print(f"Source rows: {total_source}")
    for name, count in counts.items():
        print(f"  {name}: {count}")
    print()

    if args.dry_run:
        print("Dry run complete. No data was written.")
        return

    # Connect to PostgreSQL
    pg_pool = await asyncpg.create_pool(pg_dsn, min_size=2, max_size=5)

    try:
        # Detect column intersection
        print("Detecting columns...")
        columns_map = await detect_columns(sqlite_path, pg_pool)
        print()

        # Migrate each table in FK order
        t0 = time.monotonic()
        for name in TABLE_NAMES:
            count = counts.get(name, 0)
            if count == 0:
                print(f"  {name}: skipped (0 rows)")
                continue

            cols = columns_map[name]
            print(f"  {name}: migrating {len(cols)} columns...")
            t_start = time.monotonic()
            migrated = await migrate_table(sqlite_path, pg_pool, name, cols)
            elapsed = time.monotonic() - t_start
            rate = migrated / elapsed if elapsed > 0 else 0
            print(f"  {name}: {migrated} rows in {elapsed:.1f}s ({rate:.0f} rows/s)")

        elapsed_total = time.monotonic() - t0
        print(f"\nMigration completed in {elapsed_total:.1f}s")

        # Reset sequences
        print("\n-- Resetting sequences --")
        await reset_sequences(pg_pool)

        # Verify
        if not args.skip_verify:
            ok = await verify_migration(sqlite_path, pg_pool, counts)
            if not ok:
                print("\nWARNING: Some table counts mismatch!")
                sys.exit(1)

        print("\nDone.")

    finally:
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
