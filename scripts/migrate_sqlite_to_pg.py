#!/usr/bin/env python3
"""Migrate data from legacy SQLite (m_bird.db) to PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_pg.py --sqlite-path m_bird.db
    python scripts/migrate_sqlite_to_pg.py --sqlite-path /path/to/m_bird.db --pg-dsn postgresql://...

Reads all rows from SQLite contacts, agents, conversations, messages tables
and inserts them into PostgreSQL preserving integer IDs and FK relationships.

The sync and sync_errors tables are skipped (runtime data, will be recreated by pg_sync_engine).
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

import aiosqlite
import asyncpg

BATCH_SIZE = 500

# ── Table migration order (respects FK dependencies) ────────────────────────
TABLES: list[dict[str, Any]] = [
    {
        "name": "contacts",
        "pg_columns": [
            "cnts_id",
            "cnts_name",
            "cnts_phone",
            "cnts_bird",
            "cnts_created",
            "cnts_updated",
        ],
        "sqlite_query": (
            "SELECT cnts_id, cnts_name, cnts_phone, cnts_bird, "
            "cnts_created, cnts_updated FROM contacts ORDER BY cnts_id"
        ),
    },
    {
        "name": "agents",
        "pg_columns": [
            "agnt_id",
            "agnt_name",
            "agnt_bird",
            "agnt_created",
            "agnt_updated",
            "agnt_grp",
        ],
        "sqlite_query": (
            "SELECT agnt_id, agnt_name, agnt_bird, agnt_created, agnt_updated, agnt_grp FROM agents ORDER BY agnt_id"
        ),
    },
    {
        "name": "conversations",
        "pg_columns": [
            "cnvs_id",
            "cnvs_msgcount",
            "cnvs_cnts",
            "cnvs_agnt",
            "cnvs_status",
            "cnvs_channel",
            "cnvs_bird",
            "cnvs_created",
            "cnvs_updated",
            "cnvs_last",
            "cnvs_lang",
            "cnvs_software",
            "cnvs_tax_id",
            "cnvs_dept",
            "cnvs_rating_agent",
            "cnvs_rating_nps",
            "cnvs_reopened_count",
            "cnvs_contact_reason",
            "cnvs_occurrence",
            "cnvs_description",
        ],
        "sqlite_query": (
            "SELECT cnvs_id, cnvs_msgcount, cnvs_cnts, cnvs_agnt, "
            "cnvs_status, cnvs_channel, cnvs_bird, "
            "cnvs_created, cnvs_updated, cnvs_last, "
            "cnvs_lang, cnvs_software, cnvs_tax_id, "
            "cnvs_dept, cnvs_rating_agent, cnvs_rating_nps, "
            "cnvs_reopened_count, cnvs_contact_reason, "
            "cnvs_occurrence, cnvs_description "
            "FROM conversations ORDER BY cnvs_id"
        ),
    },
    {
        "name": "messages",
        "pg_columns": [
            "msgs_id",
            "msgs_cnvs",
            "msgs_agnt",
            "msgs_direction",
            "msgs_status",
            "msgs_type",
            "msgs_content",
            "msgs_bird",
            "msgs_created",
            "msgs_updated",
        ],
        "sqlite_query": (
            "SELECT msgs_id, msgs_cnvs, msgs_agnt, "
            "msgs_direction, msgs_status, msgs_type, "
            "msgs_content, msgs_bird, "
            "msgs_created, msgs_updated "
            "FROM messages ORDER BY msgs_id"
        ),
    },
]


def build_insert_sql(table_name: str, columns: list[str]) -> str:
    """Build an INSERT ... ON CONFLICT DO NOTHING statement for asyncpg."""
    cols = ", ".join(columns)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
    return f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"


async def count_rows(sqlite_path: str) -> dict[str, int]:
    """Count all rows in each SQLite table."""
    counts: dict[str, int] = {}
    async with aiosqlite.connect(sqlite_path) as db:
        for table in TABLES:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table['name']}")
            row = await cursor.fetchone()
            counts[table["name"]] = row[0] if row else 0
    return counts


async def migrate_table(
    sqlite_path: str,
    pg_pool: asyncpg.Pool,
    table: dict,
    dry_run: bool = False,
) -> int:
    """Migrate a single table from SQLite to PostgreSQL. Returns row count."""
    table_name = table["name"]
    columns = table["pg_columns"]
    insert_sql = build_insert_sql(table_name, columns)
    total = 0

    async with aiosqlite.connect(sqlite_path) as sqlite_db:
        sqlite_db.row_factory = aiosqlite.Row
        cursor = await sqlite_db.execute(table["sqlite_query"])
        batch: list[tuple[object, ...]] = []

        async for row in cursor:
            values = tuple(row[col] for col in columns)  # type: ignore[index]
            batch.append(values)

            if len(batch) >= BATCH_SIZE:
                if not dry_run:
                    async with pg_pool.acquire() as conn:
                        await conn.executemany(insert_sql, batch)
                total += len(batch)
                batch.clear()

        # Flush remaining
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
                print(f"  Sequence {seq} → {next_val}")


async def verify_migration(sqlite_path: str, pg_pool: asyncpg.Pool) -> bool:
    """Compare row counts between SQLite and PostgreSQL."""
    print("\n── Verification ──")
    all_ok = True

    async with aiosqlite.connect(sqlite_path) as sqlite_db, pg_pool.acquire() as pg_conn:
        for table in TABLES:
            name = table["name"]
            cursor = await sqlite_db.execute(f"SELECT COUNT(*) FROM {name}")
            sqlite_row = await cursor.fetchone()
            pg_row = await pg_conn.fetchrow(f"SELECT COUNT(*) FROM {name}")
            sqlite_count = sqlite_row[0] if sqlite_row else 0
            pg_count = pg_row[0] if pg_row else 0
            match = "✓" if sqlite_count == pg_count else "✗ MISMATCH"
            if sqlite_count != pg_count:
                all_ok = False
            print(f"  {name}: SQLite={sqlite_count}  PG={pg_count}  {match}")

    return all_ok


async def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SQLite → PostgreSQL")
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
        # Try relative to project root
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
        # Migrate each table in FK order
        t0 = time.monotonic()
        for table in TABLES:
            name = table["name"]
            count = counts.get(name, 0)
            if count == 0:
                print(f"  {name}: skipped (0 rows)")
                continue

            t_start = time.monotonic()
            migrated = await migrate_table(sqlite_path, pg_pool, table)
            elapsed = time.monotonic() - t_start
            rate = migrated / elapsed if elapsed > 0 else 0
            print(f"  {name}: {migrated} rows in {elapsed:.1f}s ({rate:.0f} rows/s)")

        elapsed_total = time.monotonic() - t0
        print(f"\nMigration completed in {elapsed_total:.1f}s")

        # Reset sequences
        print("\n── Resetting sequences ──")
        await reset_sequences(pg_pool)

        # Verify
        if not args.skip_verify:
            ok = await verify_migration(sqlite_path, pg_pool)
            if not ok:
                print("\nWARNING: Some table counts mismatch!")
                sys.exit(1)

        print("\nDone.")

    finally:
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
