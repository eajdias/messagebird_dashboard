import asyncio
import logging
from datetime import datetime
from typing import Any

from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_core import PgSyncManager, month_bounds_utc, parse_dt, to_bird_iso

logger = logging.getLogger("m_bird.sync_pg")


async def sync_messages(
    manager: PgSyncManager, conn: PostgresSyncConnection, conversation_bird_id: str, date_from: str | None = None
) -> int:
    from infrastructure.sync.sync_surveys import update_conversation_surveys

    res = await _sync_messages_internal(manager, conn, conversation_bird_id, date_from)
    if res > 0:
        await update_conversation_surveys(manager, conn, conversation_bird_id)
    return res


async def _sync_messages_internal(
    manager: PgSyncManager, conn: PostgresSyncConnection, conversation_bird_id: str, date_from: str | None = None
) -> int:
    cnvs_row = await conn.fetch_one(
        "SELECT cnvs_id FROM conversations WHERE cnvs_bird = $1",
        (conversation_bird_id,),
    )
    if not cnvs_row:
        logger.error("Conversation %s not found in DB", conversation_bird_id)
        return 0

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
    limit = 20
    total_messages = 0

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

        for bid, name in agents_to_resolve.items():
            await manager.get_or_create_agent(conn, bid, name)

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

    return total_messages


async def sync_all_messages(manager: PgSyncManager, conn: PostgresSyncConnection):
    rows = await conn.fetch_all("SELECT cnvs_bird, cnvs_msgcount FROM conversations ORDER BY cnvs_updated DESC")
    total = len(rows)
    logger.info("Syncing messages for %d conversations...", total)
    start_time = __import__("time").time()
    semaphore = asyncio.Semaphore(30)

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

                return await sync_messages(manager, conn, bird_id, date_from=date_from)
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
    end_iso = to_bird_iso(next_month_start)

    rows = await conn.fetch_all(
        "SELECT cnvs_bird FROM conversations "
        "WHERE cnvs_updated >= $1::timestamp AND cnvs_updated < $2::timestamp "
        "ORDER BY cnvs_updated DESC",
        (month_start.replace(tzinfo=None), next_month_start.replace(tzinfo=None)),
    )
    total = len(rows)
    logger.info("Syncing messages for %d conversations updated in %04d-%02d...", total, year, month)
    semaphore = asyncio.Semaphore(10)

    async def fetch_with_limit(row):
        async with semaphore:
            try:
                return await sync_messages(manager, conn, row["cnvs_bird"], date_from=start_iso)
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


async def sync_messages_for_recent(manager: PgSyncManager, conn: PostgresSyncConnection, days: int = 30):
    rows = await conn.fetch_all(
        "SELECT cnvs_bird FROM conversations "
        "WHERE cnvs_updated >= (NOW() - ($1 || ' days')::interval) "
        "ORDER BY cnvs_updated DESC",
        (str(days),),
    )
    total = len(rows)
    logger.info("Syncing messages for %d conversations updated in last %d days...", total, days)
    semaphore = asyncio.Semaphore(10)

    async def fetch_with_limit(row):
        async with semaphore:
            try:
                return await sync_messages(manager, conn, row["cnvs_bird"])
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
