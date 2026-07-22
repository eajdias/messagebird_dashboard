import logging
import time
from typing import Any

from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_core import PgSyncManager, parse_dt

logger = logging.getLogger("m_bird.sync_pg")


async def sync_conversations(
    manager: PgSyncManager,
    conn: PostgresSyncConnection,
    min_date=None,
    max_date=None,
):
    logger.info(
        "Starting conversations sync (min_date=%s, max_date=%s)...",
        min_date,
        max_date,
    )
    start_time = time.time()
    limit = 20
    count = 0

    for status in ["active", "archived"]:
        offset = 0
        page_token = None

        page = 0
        while True:
            conv_params: dict[str, Any] = {"limit": limit, "offset": offset, "status": status}

            response = await manager.client.list_conversations(**conv_params)
            if "error" in response:
                await manager.log_sync_error(
                    conn, f"conversations_{status}", str(response["error"]), context=conv_params
                )
                break

            items: list[Any] = response.get("items", [])
            if not items:
                break

            pagination: dict[str, Any] = response.get("pagination", {})
            next_page_token = pagination.get("nextPageToken") or response.get("nextPageToken")
            page_token = str(next_page_token) if next_page_token else None
            offset += len(items)
            page += 1

            batch_data = []

            bird_ids_in_batch = [str(c["id"]) for c in items]
            existing_rows = await conn.fetch_all(
                "SELECT cnvs_id, cnvs_bird, cnvs_status, cnvs_agnt, cnvs_reopened_count "
                "FROM conversations WHERE cnvs_bird = ANY($1::varchar[])",
                (bird_ids_in_batch,),
            )
            existing_map = {
                r["cnvs_bird"]: {
                    "id": r["cnvs_id"],
                    "status": r["cnvs_status"],
                    "agnt": r["cnvs_agnt"],
                    "reopened": r["cnvs_reopened_count"],
                }
                for r in existing_rows
            }

            contacts_to_resolve: dict[str, tuple[str | None, str]] = {}
            for c in items:
                c_id = c.get("contactId")
                if c_id and c_id not in manager._contact_cache:
                    contact_data = c.get("contact", {})
                    contact_name = contact_data.get("displayName") or None
                    if contact_name and str(contact_name).strip().lower() in ("none", "null", ""):
                        contact_name = None
                    contacts_to_resolve[c_id] = (contact_name, str(contact_data.get("msisdn", "")))

            if contacts_to_resolve:
                new_contacts_data = [(bid, name, phone) for bid, (name, phone) in contacts_to_resolve.items()]
                async with conn.transaction():
                    await conn.execute_many(
                        "INSERT INTO contacts (cnts_bird, cnts_name, cnts_phone) VALUES ($1, $2, $3) "
                        "ON CONFLICT (cnts_bird) DO NOTHING",
                        new_contacts_data,
                    )
                bids = list(contacts_to_resolve.keys())
                rows = await conn.fetch_all(
                    "SELECT cnts_id, cnts_bird FROM contacts WHERE cnts_bird = ANY($1::varchar[])", (bids,)
                )
                for r in rows:
                    manager._contact_cache[r["cnts_bird"]] = r["cnts_id"]

            for c in items:
                updated_at_str = c.get("updatedDatetime")
                updated_dt = parse_dt(updated_at_str) if updated_at_str else None

                cnvs_created_raw = c.get("createdDatetime")
                if max_date and cnvs_created_raw and cnvs_created_raw >= max_date:
                    continue
                if min_date and cnvs_created_raw and cnvs_created_raw < min_date:
                    continue

                cnvs_bird = c["id"]
                cnts_id = manager._contact_cache.get(c.get("contactId"))
                cnvs_msgcount = c.get("messages", {}).get("totalCount", 0)
                cnvs_status = c.get("status")
                cnvs_channel = c.get("lastUsedChannelId")
                cnvs_created = parse_dt(c.get("createdDatetime"))
                cnvs_updated = updated_dt
                cnvs_last = parse_dt(c.get("lastReceivedDatetime"))

                old_data = existing_map.get(cnvs_bird)
                reopened_increment = 0
                if (
                    old_data
                    and old_data["status"] != cnvs_status
                    and old_data["status"] == "archived"
                    and cnvs_status == "active"
                ):
                    reopened_increment = 1

                assigned = c.get("assignedTo") or {}
                new_agnt_bird = assigned.get("id") if isinstance(assigned, dict) else None
                new_agnt_id = manager._agent_cache.get(new_agnt_bird) if new_agnt_bird else None

                batch_data.append(
                    (
                        cnvs_bird,
                        cnts_id,
                        new_agnt_id,
                        cnvs_status,
                        cnvs_channel,
                        cnvs_created,
                        cnvs_updated,
                        cnvs_last,
                        cnvs_msgcount,
                        reopened_increment,
                    )
                )

            if batch_data:
                async with conn.transaction():
                    await conn.execute_many(
                        "INSERT INTO conversations "
                        "(cnvs_bird, cnvs_cnts, cnvs_agnt, cnvs_status, cnvs_channel, "
                        "cnvs_created, cnvs_updated, cnvs_last, cnvs_msgcount, cnvs_reopened_count) "
                        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) "
                        "ON CONFLICT (cnvs_bird) DO UPDATE SET "
                        "cnvs_msgcount = EXCLUDED.cnvs_msgcount, "
                        "cnvs_status = EXCLUDED.cnvs_status, "
                        "cnvs_channel = EXCLUDED.cnvs_channel, "
                        "cnvs_updated = EXCLUDED.cnvs_updated, "
                        "cnvs_last = EXCLUDED.cnvs_last, "
                        "cnvs_reopened_count = conversations.cnvs_reopened_count + EXCLUDED.cnvs_reopened_count, "
                        "cnvs_agnt = COALESCE(EXCLUDED.cnvs_agnt, conversations.cnvs_agnt)",
                        batch_data,
                    )
                count += len(batch_data)

            if page % 5 == 0:
                logger.info("  convs %s: page %d, %d fetched so far...", status, page, count)

            if len(items) < limit:
                break

            page_max = max(c.get("createdDatetime", "") or "" for c in items)
            if min_date and page_max < min_date:
                break

            if status == "active":
                await manager.save_sync_progress(conn, "conversations", cursor=None, offset=offset)

    duration = time.time() - start_time
    await manager.update_sync_state(
        conn, "conversations", duration=duration, records_count=count, cursor=None, offset=0
    )
    logger.info("Conversations sync completed: %d items in %.1fs", count, duration)
