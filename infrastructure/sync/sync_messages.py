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
    """Sync messages. Returns (count, raw_messages_list)."""
    if cnvs_id is None:
        cnvs_row = await conn.fetch_one(
            "SELECT cnvs_id FROM conversations WHERE cnvs_bird = $1",
            (conversation_bird_id,),
        )
        if not cnvs_row:
            logger.error("Conversation %s not found in DB", conversation_bird_id)
            return 0, []
        cnvs_id = cnvs_row["cnvs_id"]

    if date_from is None:
        last_msg = await conn.fetch_one(
            "SELECT msgs_created FROM messages WHERE msgs_cnvs = $1 ORDER BY msgs_created DESC LIMIT 1",
            (cnvs_id,),
        )
        if last_msg and last_msg["msgs_created"]:
            df = last_msg["msgs_created"]
            date_from = df.isoformat() if isinstance(df, datetime) else str(df)
            if "+" in date_from:
                date_from = date_from.split("+")[0] + "Z"
            elif not date_from.endswith("Z"):
                date_from += "Z"

    offset = 0
    limit = 20  # MessageBird messages API max is 20
    total_messages = 0
    all_raw_messages: list[dict[str, Any]] = []

    while True:
        response = await manager.client.get_messages(
            conversation_bird_id, limit=limit, offset=offset, date_from=date_from
        )

        if "error" in response:
            await manager.log_sync_error(
                conn,
                "messages",
                str(response["error"]),
                context={"cnvs_bird": conversation_bird_id, "offset": offset},
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

            batch_params.append(
                (
                    cnvs_id,
                    agnt_id,
                    direction,
                    m_data["status"],
                    m_data["type"],
                    m_data["content"],
                    m_data["id"],
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
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                    "ON CONFLICT (msgs_bird) DO UPDATE SET "
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
        offset += len(items)

    return total_messages, all_raw_messages


async def sync_all_messages(manager: PgSyncManager, conn: PostgresSyncConnection):
    rows = await conn.fetch_all("SELECT cnvs_bird, cnvs_msgcount FROM conversations ORDER BY cnvs_updated DESC")
    total = len(rows)
    logger.info("Syncing messages for %d conversations...", total)
    start_time = __import__("time").time()
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
            try:
                bird_id = row["cnvs_bird"]
                remote_count = row["cnvs_msgcount"]
                local_count_row = await conn.fetch_one(
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

                count, _ = await sync_messages(manager, conn, bird_id, date_from=date_from)
                return count
            except Exception as e:
                logger.error("Error syncing messages for %s: %s", row["cnvs_bird"], e)
                return 0

    tasks = [fetch_with_limit(row) for row in rows]
    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i : i + chunk_size]
        results = await asyncio.gather(*chunk)
        msg_count += sum(results)
        logger.info("  messages: %d/%d conversations done (%d msgs)...", min(i + chunk_size, total), total, msg_count)

    elapsed = __import__("time").time() - start_time
    await manager.update_sync_state(conn, "messages", duration=elapsed, records_count=msg_count)
    logger.info("All messages sync completed: %d convs, %d messages in %.1fs", total, msg_count, elapsed)


async def sync_messages_for_month(manager: PgSyncManager, conn: PostgresSyncConnection, year: int, month: int) -> int:
    month_start, next_month_start = month_bounds_utc(year, month)
    start_iso = to_bird_iso(month_start)

    # Batch pre-fetch: cnvs_bird, cnvs_id, and last message date in one query
    rows = await conn.fetch_all(
        "SELECT c.cnvs_bird, c.cnvs_id, "
        "  (SELECT MAX(m.msgs_created) FROM messages m WHERE m.msgs_cnvs = c.cnvs_id) as last_msg_date "
        "FROM conversations c "
        "WHERE c.cnvs_created >= $1::timestamp AND c.cnvs_created < $2::timestamp "
        "ORDER BY c.cnvs_created DESC",
        (month_start.replace(tzinfo=None), next_month_start.replace(tzinfo=None)),
    )
    total = len(rows)
    logger.info("Syncing messages for %d conversations created in %04d-%02d...", total, year, month)
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
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
                    conn,
                    row["cnvs_bird"],
                    date_from=date_from,
                    cnvs_id=row["cnvs_id"],
                )
                return count
            except Exception as e:
                logger.error("Error syncing %s: %s", row["cnvs_bird"], e)
                return 0

    tasks = [fetch_with_limit(row) for row in rows]
    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i : i + chunk_size]
        results = await asyncio.gather(*chunk)
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
    logger.info(
        "Syncing messages for %d conversations updated between %s and %s...",
        total,
        start_naive.isoformat(),
        end_naive.isoformat(),
    )
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
            try:
                count, _ = await sync_messages(manager, conn, row["cnvs_bird"], date_from=start_iso)
                return count
            except Exception as e:
                logger.error("Error syncing %s: %s", row["cnvs_bird"], e)
                return 0

    tasks = [fetch_with_limit(row) for row in rows]
    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i : i + chunk_size]
        results = await asyncio.gather(*chunk)
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
    logger.info("Syncing messages for %d conversations updated in last %d days...", total, days)
    semaphore = asyncio.Semaphore(2)

    async def fetch_with_limit(row):
        async with semaphore:
            try:
                count, _ = await sync_messages(manager, conn, row["cnvs_bird"])
                return count
            except Exception as e:
                logger.error("Error syncing %s: %s", row["cnvs_bird"], e)
                return 0

    tasks = [fetch_with_limit(row) for row in rows]
    msg_count = 0
    chunk_size = 1000

    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i : i + chunk_size]
        results = await asyncio.gather(*chunk)
        msg_count += sum(results)
        logger.info("  messages: %d/%d conversations done", min(i + chunk_size, total), total)

    logger.info("Recent messages sync completed: %d conversations, %d messages.", total, msg_count)
