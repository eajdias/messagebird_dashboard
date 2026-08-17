"""Idempotent backfill of conversation metrics (FRT / ART).

Recomputes first-response time and average-response time for every
conversation directly from the raw messages table, using the same
definition as the conversations list query (first agent reply with a
department group, last client message within the 24h window before the
first reply, capped at MAX_ART_MINUTES).

Idempotent: re-running always produces the same deterministic values,
overwriting stale ones, so it can be safely executed after every sync.
"""

import logging

from domain import constants
from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_core import PgSyncManager

logger = logging.getLogger("m_bird.sync_pg")

METRICS_BACKFILL_SQL = f"""
WITH first_resp AS (
    SELECT m.msgs_cnvs, MIN(m.msgs_created) AS sent_at
    FROM messages m
    LEFT JOIN agents a_resp ON a_resp.agnt_id = m.msgs_agnt
    WHERE m.msgs_direction = 'sent'
      AND m.msgs_agnt IS NOT NULL
      AND a_resp.agnt_grp IS NOT NULL
    GROUP BY m.msgs_cnvs
),
last_client AS (
    SELECT fr.msgs_cnvs, MAX(m.msgs_created) AS client_at
    FROM first_resp fr
    JOIN messages m ON m.msgs_cnvs = fr.msgs_cnvs
    WHERE m.msgs_direction = 'received'
      AND m.msgs_created < fr.sent_at
      AND m.msgs_created >= fr.sent_at - INTERVAL '24 hours'
    GROUP BY fr.msgs_cnvs
),
metrics AS (
    SELECT
        c.cnvs_id,
        CASE
            WHEN fr.sent_at IS NOT NULL
             AND lc.client_at IS NOT NULL
             AND fr.sent_at > lc.client_at
            THEN ROUND(
                LEAST(
                    EXTRACT(EPOCH FROM (fr.sent_at - lc.client_at)) / 60.0,
                    {constants.MAX_ART_MINUTES}.0
                ),
                1
            )::numeric
            ELSE NULL
        END AS art
    FROM conversations c
    LEFT JOIN first_resp fr ON fr.msgs_cnvs = c.cnvs_id
    LEFT JOIN last_client lc ON lc.msgs_cnvs = c.cnvs_id
)
UPDATE conversations c SET
    cnvs_frt_minutes = metrics.art,
    cnvs_art_minutes = metrics.art
FROM metrics
WHERE metrics.cnvs_id = c.cnvs_id
"""


async def backfill_conversation_metrics(
    manager: PgSyncManager,
    conn: PostgresSyncConnection,
) -> int:
    """Recompute FRT/ART for all conversations from raw messages.

    Idempotent by design: every run recomputes the full set of
    conversations and overwrites the stored values deterministically.
    Returns the number of conversations that now have an ART value.
    """
    await conn.execute_query(METRICS_BACKFILL_SQL)
    row = await conn.fetch_one("SELECT COUNT(*) AS n FROM conversations WHERE cnvs_art_minutes IS NOT NULL")
    count = int(row["n"]) if row else 0
    logger.info("Conversation metrics backfill completed: %d conversations with ART.", count)
    return count
