import logging
import time
from typing import Any

from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_core import PgSyncManager, parse_dt

logger = logging.getLogger("m_bird.sync_pg")


async def sync_contacts(manager: PgSyncManager, conn: PostgresSyncConnection):
    logger.info("Starting contacts sync...")
    start_time = time.time()
    offset = 0
    limit = 20
    processed_count = 0
    page = 0
    while True:
        response = await manager.client.list_contacts(limit=limit, offset=offset)
        if "error" in response:
            await manager.log_sync_error(conn, "contacts", str(response["error"]), context={"offset": offset})
            break
        items: list[dict[str, Any]] = response.get("items", [])
        if not items:
            break
        contacts_data = []
        for c in items:
            phone = c.get("phone") or str(c.get("msisdn", ""))
            if phone in ("None", "null", ""):
                phone = None
            contact_name = c.get("displayName") or None
            if contact_name and str(contact_name).strip().lower() in ("none", "null", ""):
                contact_name = None
            contacts_data.append(
                (contact_name, phone, c.get("id"), parse_dt(c.get("createdAt")), parse_dt(c.get("updatedAt")))
            )
        if contacts_data:
            async with conn.transaction():
                await conn.execute_many(
                    "INSERT INTO contacts (cnts_name, cnts_phone, cnts_bird, cnts_created, cnts_updated) "
                    "VALUES ($1, $2, $3, $4, $5) "
                    "ON CONFLICT (cnts_bird) DO UPDATE SET cnts_name = EXCLUDED.cnts_name, "
                    "cnts_phone = EXCLUDED.cnts_phone, cnts_updated = EXCLUDED.cnts_updated",
                    contacts_data,
                )
            processed_count += len(contacts_data)
            bird_ids = [c[2] for c in contacts_data]
            if bird_ids:
                rows = await conn.fetch_all(
                    "SELECT cnts_id, cnts_bird FROM contacts WHERE cnts_bird = ANY($1::varchar[])", (bird_ids,)
                )
                for row in rows:
                    manager._contact_cache[row["cnts_bird"]] = row["cnts_id"]
        page += 1
        if page % 10 == 0:
            logger.info("  contacts: %d fetched (%d pages)...", processed_count, page)
        if len(items) < limit:
            break
        offset += len(items)
    duration = time.time() - start_time
    await manager.update_sync_state(conn, "contacts", duration=duration, records_count=processed_count)
    logger.info("Contacts sync completed: %d items in %.1fs", processed_count, duration)
