"""Idempotent backfill of conversation metrics (FRT / ART).

Recomputes first-response time and average-response time for every
conversation directly from the raw messages table.

FRT: last client message within the 24h window before the first agent
reply (with a department group) -> that first reply, capped at MAX_ART_MINUTES.

ART: mean of every client-message -> next-agent-reply delta, capped per
pair at MAX_ART_MINUTES.

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
frt AS (
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
        END AS frt_minutes
    FROM conversations c
    LEFT JOIN first_resp fr ON fr.msgs_cnvs = c.cnvs_id
    LEFT JOIN last_client lc ON lc.msgs_cnvs = c.cnvs_id
),
msg_pairs AS (
    SELECT
        msgs_cnvs,
        msgs_created,
        msgs_direction,
        LAG(msgs_created) OVER (PARTITION BY msgs_cnvs ORDER BY msgs_created) AS prev_created,
        LAG(msgs_direction) OVER (PARTITION BY msgs_cnvs ORDER BY msgs_created) AS prev_direction
    FROM messages
),
resp_pairs AS (
    SELECT
        msgs_cnvs,
        LEAST(
            EXTRACT(EPOCH FROM (msgs_created - prev_created)) / 60.0,
            {constants.MAX_ART_MINUTES}.0
        ) AS delta_min
    FROM msg_pairs
    WHERE msgs_direction = 'sent'
      AND prev_direction = 'received'
      AND msgs_created > prev_created
),
art AS (
    SELECT msgs_cnvs, ROUND(AVG(delta_min), 1)::numeric AS art_minutes
    FROM resp_pairs
    GROUP BY msgs_cnvs
)
UPDATE conversations c SET
    cnvs_frt_minutes = frt.frt_minutes,
    cnvs_art_minutes = art.art_minutes
FROM frt
LEFT JOIN art ON art.msgs_cnvs = frt.cnvs_id
WHERE frt.cnvs_id = c.cnvs_id
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
