import asyncio
import logging
from datetime import datetime
from typing import Any

from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_core import PgSyncManager, month_bounds_utc, parse_dt, to_bird_iso

logger = logging.getLogger("m_bird.sync_pg")


async def sync_messages(
    manager: PgSyncManager,
    conn: PostgresSyncConnection,
    conversation_bird_id: str,
    date_from: str | None = None,
    cnvs_id: int | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Sync messages for a conversation. Returns (message_count, raw_messages_list).

    If cnvs_id is provided, skip the DB lookup for conversation ID.
    If date_from is provided, skip the DB lookup for last message date.
    """
    from infrastructure.sync.sync_surveys import update_conversation_surveys

    res, raw_messages = await _sync_messages_internal(manager, conn, conversation_bird_id, date_from, cnvs_id)
    if res > 0:
        await update_conversation_surveys(manager, conn, conversation_bird_id, raw_messages)
    return res, raw_messages


async def _sync_messages_internal(
    manager: PgSyncManager,
    conn: PostgresSyncConnection,
    conversation_bird_id: str,
    date_from: str | None = None,
    cnvs_id: int | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Sync messages. Returns (count, raw_messages_list).

    The MessageBird messages API returns messages in reverse chronological order
    (newest first) and paginates with limit=20. The dateFrom parameter is accepted
    but does NOT filter results — totalCount remains the same regardless.
    We rely on ON CONFLICT DO UPDATE for idempotency.
    """
    if cnvs_id is None:
        cnvs_row = await conn.fetch_one(
            "SELECT cnvs_id FROM conversations WHERE cnvs_bird = $1",
            (conversation_bird_id,),
        )
        if not cnvs_row:
            logger.error("Conversation %s not found in DB", conversation_bird_id)
            return 0, []
        cnvs_id = cnvs_row["cnvs_id"]

    page_token: str | None = None
    limit = 20  # MessageBird messages API max is 20
    total_messages = 0
    all_raw_messages: list[dict[str, Any]] = []

    while True:
        response = await manager.client.get_messages(
            conversation_bird_id, limit=limit, date_from=date_from, page_token=page_token
        )

        if "error" in response:
            error_msg = str(response["error"])
            error_details = str(response.get("details", ""))
            if "410" in error_msg and "deleted" in error_details.lower():
                await conn.execute_query(
                    "UPDATE conversations SET cnvs_status = 'archived' WHERE cnvs_bird = $1 AND cnvs_status = 'active'",
                    (conversation_bird_id,),
                )
                logger.info("Conversation %s deleted on Bird, marked as archived", conversation_bird_id)
            else:
                await manager.log_sync_error(
                    conn,
                    "messages",
                    error_msg,
                    context={"cnvs_bird": conversation_bird_id, "page_token": page_token},
                )
            break

        items: list[dict[str, Any]] = response.get("items", [])
        if not items:
            break

        agents_to_resolve: dict[str, str] = {}
        all_messages = []

        for m in items:
            direction = m.get("direction")
            content_obj = m.get("content")
            content_text = ""
            if isinstance(content_obj, dict):
                content_text = content_obj.get("text", "") or content_obj.get("hsm", {}).get("elementName", "")
            else:
                content_text = str(content_obj) if content_obj else ""

            if direction == "sent":
                source = m.get("source", {})
                agent = source.get("inboxAgent")
                if agent and agent.get("id"):
                    agent_bid = agent["id"]
                    if agent_bid not in manager._agent_cache:
                        agents_to_resolve[agent_bid] = agent.get("fullName") or agent.get("firstName") or "Unknown"

            all_messages.append(
                {
                    "id": m.get("id"),
                    "direction": direction,
                    "status": m.get("status"),
                    "type": m.get("type"),
                    "content": content_text,
                    "created": m.get("createdDatetime"),
                    "updated": m.get("updatedDatetime"),
                    "source": m.get("source", {}),
                }
            )

        all_raw_messages.extend(items)

        # Batch resolve all new agents at once (instead of per-agent)
        if agents_to_resolve:
            await manager.batch_resolve_agents(conn, agents_to_resolve)

        batch_params = []
        last_agent_id = None

        for m_data in all_messages:
            direction = m_data["direction"]
            agnt_id = None
            if direction == "sent":
                agent = m_data["source"].get("inboxAgent")
                if agent and agent.get("id"):
                    agnt_id = manager._agent_cache.get(agent["id"])
                    last_agent_id = agnt_id

            status_val = m_data["status"]
            type_val = m_data["type"]
            content_val = m_data["content"]
            bird_id_val = m_data["id"]

            batch_params.append(
                (
                    int(cnvs_id),
                    int(agnt_id) if agnt_id is not None else None,
                    str(direction or ""),
                    str(status_val) if status_val is not None else "",
                    str(type_val) if type_val is not None else "",
                    str(content_val) if content_val is not None else "",
                    str(bird_id_val),
                    parse_dt(m_data["created"]),
                    parse_dt(m_data["updated"]),
                )
            )

        if batch_params:
            async with conn.transaction():
                await conn.execute_many(
                    "INSERT INTO messages "
                    "(msgs_cnvs, msgs_agnt, msgs_direction, msgs_status, msgs_type, "
                    "msgs_content, msgs_bird, msgs_created, msgs_updated) "
                    "VALUES ($1::int4, $2::int4, $3::varchar, $4::varchar, $5::varchar, "
                    "$6::text, $7::varchar, $8::timestamp, $9::timestamp) "
                    "ON CONFLICT (msgs_cnvs, msgs_bird) DO UPDATE SET "
                    "msgs_status = EXCLUDED.msgs_status, msgs_updated = EXCLUDED.msgs_updated",
                    batch_params,
                )
                if last_agent_id:
                    await conn.execute_query(
                        "UPDATE conversations SET cnvs_agnt = $1 WHERE cnvs_id = $2",
                        (last_agent_id, cnvs_id),
                    )
            total_messages += len(batch_params)

        if len(items) < limit:
            break
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return total_messages, all_raw_messages


async def sync_all_messages(manager: PgSyncManager, conn: PostgresSyncConnection):
    rows = await conn.fetch_all("SELECT cnvs_bird, cnvs_msgcount FROM conversations ORDER BY cnvs_updated DESC")
    total = len(rows)
    raw_pool = conn._pool  # noqa: SLF001
    logger.info("Syncing messages for %d conversations...", total)
    start_time = __import__("time").time()
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
            task_conn = PostgresSyncConnection(raw_pool)
            try:
                bird_id = row["cnvs_bird"]
                remote_count = row["cnvs_msgcount"]
                local_count_row = await task_conn.fetch_one(
                    "SELECT COUNT(*) as count, MAX(msgs_created) as last_msg_date "
                    "FROM messages WHERE msgs_cnvs = (SELECT cnvs_id FROM conversations WHERE cnvs_bird = $1)",
                    (bird_id,),
                )
                local_count = local_count_row["count"] if local_count_row else 0
                last_msg_date = local_count_row["last_msg_date"] if local_count_row else None

                if remote_count is not None and local_count == remote_count and remote_count > 0:
                    return 0

                date_from = None
                if local_count > 0 and last_msg_date:
                    date_from = last_msg_date.isoformat() if isinstance(last_msg_date, datetime) else str(last_msg_date)

                count, _ = await sync_messages(manager, task_conn, bird_id, date_from=date_from)
                return count
            except Exception as e:
                logger.error("Error syncing messages for %s: %s", row["cnvs_bird"], e)
                return 0

    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        results = await asyncio.gather(*[fetch_with_limit(row) for row in chunk])
        msg_count += sum(results)
        logger.info("  messages: %d/%d conversations done (%d msgs)...", min(i + chunk_size, total), total, msg_count)

    elapsed = __import__("time").time() - start_time
    await manager.update_sync_state(conn, "messages", duration=elapsed, records_count=msg_count)
    logger.info("All messages sync completed: %d convs, %d messages in %.1fs", total, msg_count, elapsed)


async def sync_messages_for_month(manager: PgSyncManager, conn: PostgresSyncConnection, year: int, month: int) -> int:
    month_start, next_month_start = month_bounds_utc(year, month)
    start_iso = to_bird_iso(month_start)

    # Batch pre-fetch: cnvs_bird, cnvs_id, and last message date using JOIN (not correlated subquery)
    rows = await conn.fetch_all(
        "SELECT c.cnvs_bird, c.cnvs_id, lm.last_msg_date "
        "FROM conversations c "
        "LEFT JOIN LATERAL ("
        "  SELECT MAX(m.msgs_created) AS last_msg_date "
        "  FROM messages m WHERE m.msgs_cnvs = c.cnvs_id"
        ") lm ON true "
        "WHERE c.cnvs_created >= $1::timestamp AND c.cnvs_created < $2::timestamp "
        "ORDER BY c.cnvs_created DESC",
        (month_start.replace(tzinfo=None), next_month_start.replace(tzinfo=None)),
    )
    total = len(rows)
    raw_pool = conn._pool  # noqa: SLF001
    logger.info("Syncing messages for %d conversations created in %04d-%02d...", total, year, month)
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
            task_conn = PostgresSyncConnection(raw_pool)
            try:
                # Determine date_from: use last_msg_date if available, otherwise use start_iso
                date_from = start_iso
                if row["last_msg_date"]:
                    lm = row["last_msg_date"]
                    date_from = lm.isoformat() if isinstance(lm, datetime) else str(lm)
                    if "+" in date_from:
                        date_from = date_from.split("+")[0] + "Z"
                    elif not date_from.endswith("Z"):
                        date_from += "Z"

                count, _ = await sync_messages(
                    manager,
                    task_conn,
                    row["cnvs_bird"],
                    date_from=date_from,
                    cnvs_id=row["cnvs_id"],
                )
                return count
            except Exception as e:
                logger.error("Error syncing %s: %s", row["cnvs_bird"], e)
                return 0

    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        results = await asyncio.gather(*[fetch_with_limit(row) for row in chunk])
        msg_count += sum(results)
        logger.info("  messages: %d/%d conversations done", min(i + chunk_size, total), total)

    logger.info(
        "Monthly messages sync completed: %d conversations, %d messages from %04d-%02d.", total, msg_count, year, month
    )
    return msg_count


async def sync_messages_for_range(
    manager: PgSyncManager,
    conn: PostgresSyncConnection,
    start_dt: datetime,
    end_dt: datetime,
) -> int:
    """Sync messages for conversations updated within [start_dt, end_dt)."""
    start_naive = start_dt.replace(tzinfo=None)
    end_naive = end_dt.replace(tzinfo=None)
    start_iso = to_bird_iso(start_dt)
    rows = await conn.fetch_all(
        "SELECT cnvs_bird FROM conversations "
        "WHERE cnvs_updated >= $1::timestamp AND cnvs_updated < $2::timestamp "
        "ORDER BY cnvs_updated DESC",
        (start_naive, end_naive),
    )
    total = len(rows)
    raw_pool = conn._pool  # noqa: SLF001
    logger.info(
        "Syncing messages for %d conversations updated between %s and %s...",
        total,
        start_naive.isoformat(),
        end_naive.isoformat(),
    )
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
            task_conn = PostgresSyncConnection(raw_pool)
            try:
                count, _ = await sync_messages(manager, task_conn, row["cnvs_bird"], date_from=start_iso)
                return count
            except Exception as e:
                logger.error("Error syncing %s: %s", row["cnvs_bird"], e)
                return 0

    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        results = await asyncio.gather(*[fetch_with_limit(row) for row in chunk])
        msg_count += sum(results)
        logger.info("  messages: %d/%d conversations done", min(i + chunk_size, total), total)

    logger.info("Range messages sync completed: %d conversations, %d messages.", total, msg_count)
    return msg_count


async def sync_messages_for_recent(manager: PgSyncManager, conn: PostgresSyncConnection, days: int = 30):
    rows = await conn.fetch_all(
        "SELECT cnvs_bird FROM conversations "
        "WHERE cnvs_updated >= (NOW() - ($1 || ' days')::interval) "
        "ORDER BY cnvs_updated DESC",
        (str(days),),
    )
    total = len(rows)
    raw_pool = conn._pool  # noqa: SLF001
    logger.info("Syncing messages for %d conversations updated in last %d days...", total, days)
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
            task_conn = PostgresSyncConnection(raw_pool)
            try:
                count, _ = await sync_messages(manager, task_conn, row["cnvs_bird"])
                return count
            except Exception as e:
                logger.error("Error syncing %s: %s", row["cnvs_bird"], e)
                return 0

    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        results = await asyncio.gather(*[fetch_with_limit(row) for row in chunk])
        msg_count += sum(results)
        logger.info("  messages: %d/%d conversations done", min(i + chunk_size, total), total)

    logger.info("Recent messages sync completed: %d conversations, %d messages.", total, msg_count)
    return msg_count


async def sync_incomplete_conversations(
    manager: PgSyncManager,
    conn: PostgresSyncConnection,
    *,
    batch_limit: int = 5000,
    max_conversations: int | None = None,
) -> int:
    """Re-sync conversations where local message count < remote count.

    Finds conversations with incomplete message syncs (typically caused by
    interrupted syncs where pagination stopped mid-way) and re-fetches all
    messages. The ON CONFLICT DO UPDATE in _sync_messages_internal handles
    already-stored messages idempotently.

    Returns total new messages synced.
    """
    raw_pool = conn._pool  # noqa: SLF001

    rows = await conn.fetch_all(
        """
        SELECT c.cnvs_id, c.cnvs_bird, c.cnvs_msgcount,
               COUNT(m.msgs_id) AS local_count
        FROM conversations c
        LEFT JOIN messages m ON m.msgs_cnvs = c.cnvs_id
        WHERE c.cnvs_msgcount IS NOT NULL
          AND c.cnvs_msgcount > 0
        GROUP BY c.cnvs_id, c.cnvs_bird, c.cnvs_msgcount
        HAVING COUNT(m.msgs_id) < c.cnvs_msgcount
        ORDER BY (c.cnvs_msgcount - COUNT(m.msgs_id)) DESC
        LIMIT $1
        """,
        (batch_limit if max_conversations is None else min(batch_limit, max_conversations),),
    )
    total = len(rows)
    if total == 0:
        logger.info("No incomplete conversations found.")
        return 0

    logger.info("Found %d incomplete conversations, re-syncing messages...", total)
    semaphore = asyncio.Semaphore(5)
    msg_count = 0
    chunk_size = 50

    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        chunk_tasks = [_sync_one_incomplete(manager, raw_pool, row, semaphore) for row in chunk]
        results = await asyncio.gather(*chunk_tasks)
        msg_count += sum(results)
        logger.info(
            "  incomplete sync: %d/%d conversations done (%d msgs)",
            min(i + chunk_size, total),
            total,
            msg_count,
        )

    logger.info("Incomplete conversations sync completed: %d conversations, %d messages.", total, msg_count)
    return msg_count


async def _sync_one_incomplete(
    manager: PgSyncManager,
    raw_pool: Any,
    row: Any,
    semaphore: asyncio.Semaphore,
) -> int:
    async with semaphore:
        task_conn = PostgresSyncConnection(raw_pool)
        try:
            count, _ = await sync_messages(
                manager,
                task_conn,
                row["cnvs_bird"],
                cnvs_id=row["cnvs_id"],
            )
            return count
        except Exception as e:
            logger.error("Error re-syncing %s: %s", row["cnvs_bird"], e)
            return 0
