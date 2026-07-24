from domain.constants import MAX_ART_MINUTES

SURVEY_DATA_METADATA_QUERY = """
    SELECT
        ca.agnt_name AS conversation_agent_name,
        ma.agnt_name AS message_agent_name,
        ca.agnt_grp  AS agent_group,
        c.cnts_id,
        c.cnts_name,
        c.cnts_phone,
        cv.cnvs_id,
        cv.cnvs_created,
        cv.cnvs_updated,
        cv.cnvs_status,
        cv.cnvs_lang,
        cv.cnvs_software,
        cv.cnvs_tax_id,
        cv.cnvs_dept,
        cv.cnvs_rating_agent,
        cv.cnvs_rating_nps,
        cv.cnvs_contact_reason,
        cv.cnvs_occurrence,
        cv.cnvs_channel,
        cv.cnvs_description,
        m.msgs_id,
        m.msgs_created,
        m.msgs_direction,
        m.msgs_agnt
    FROM messages m
    JOIN conversations cv ON m.msgs_cnvs = cv.cnvs_id
    LEFT JOIN agents ca ON cv.cnvs_agnt = ca.agnt_id
    LEFT JOIN agents ma ON m.msgs_agnt = ma.agnt_id
    JOIN contacts c ON cv.cnvs_cnts = c.cnts_id
    WHERE (cv.cnvs_created::timestamp BETWEEN $1::timestamp AND $2::timestamp)
       OR (cv.cnvs_updated::timestamp BETWEEN $3::timestamp AND $4::timestamp)
    ORDER BY cv.cnvs_id, m.msgs_created ASC
"""

SURVEY_DATA_METADATA_QUERY_ALL = """
    SELECT
        ca.agnt_name AS conversation_agent_name,
        ma.agnt_name AS message_agent_name,
        ca.agnt_grp  AS agent_group,
        c.cnts_id,
        c.cnts_name,
        c.cnts_phone,
        cv.cnvs_id,
        cv.cnvs_created,
        cv.cnvs_updated,
        cv.cnvs_status,
        cv.cnvs_lang,
        cv.cnvs_software,
        cv.cnvs_tax_id,
        cv.cnvs_dept,
        cv.cnvs_rating_agent,
        cv.cnvs_rating_nps,
        cv.cnvs_contact_reason,
        cv.cnvs_occurrence,
        cv.cnvs_channel,
        cv.cnvs_description,
        m.msgs_id,
        m.msgs_created,
        m.msgs_direction,
        m.msgs_agnt
    FROM messages m
    JOIN conversations cv ON m.msgs_cnvs = cv.cnvs_id
    LEFT JOIN agents ca ON cv.cnvs_agnt = ca.agnt_id
    LEFT JOIN agents ma ON m.msgs_agnt = ma.agnt_id
    JOIN contacts c ON cv.cnvs_cnts = c.cnts_id
    ORDER BY cv.cnvs_id, m.msgs_created ASC
"""

AGENT_MSG_CNVS_QUERY = """
    SELECT
        cv.cnvs_id,
        cv.cnvs_created,
        cv.cnvs_dept,
        cv.cnvs_contact_reason,
        cv.cnvs_rating_nps,
        cv.cnvs_occurrence,
        c.cnts_name,
        c.cnts_phone,
        m.msgs_created,
        m.msgs_direction,
        a.agnt_name
    FROM conversations cv
    JOIN contacts c ON cv.cnvs_cnts = c.cnts_id
    JOIN messages m ON cv.cnvs_id = m.msgs_cnvs
    LEFT JOIN agents a ON m.msgs_agnt = a.agnt_id
    WHERE (cv.cnvs_created::timestamp BETWEEN $1::timestamp AND $2::timestamp)
       OR (cv.cnvs_updated::timestamp BETWEEN $3::timestamp AND $4::timestamp)
    ORDER BY cv.cnvs_id, m.msgs_created ASC
"""

OS_DATA_QUERY = """
    SELECT
        c.cnvs_id,
        c.cnvs_bird,
        c.cnvs_agnt,
        c.cnvs_msgcount,
        c.cnvs_created,
        c.cnvs_updated,
        c.cnvs_dept,
        c.cnvs_contact_reason,
        c.cnvs_occurrence,
        c.cnvs_software,
        c.cnvs_rating_agent,
        c.cnvs_rating_nps,
        c.cnvs_reopened_count,
        c.cnvs_description,
        c.cnvs_tax_id,
        ct.cnts_id,
        ct.cnts_name,
        ct.cnts_phone,
        a.agnt_name,
        a.agnt_grp
    FROM conversations c
    LEFT JOIN contacts ct ON ct.cnts_id = c.cnvs_cnts
    LEFT JOIN agents a ON a.agnt_id = c.cnvs_agnt
    WHERE (c.cnvs_created >= $1::timestamp AND c.cnvs_created <= $2::timestamp)
       OR (c.cnvs_updated >= $3::timestamp AND c.cnvs_updated <= $4::timestamp)
    ORDER BY c.cnvs_created
"""

OS_DATA_QUERY_ALL = """
    SELECT
        c.cnvs_id,
        c.cnvs_bird,
        c.cnvs_agnt,
        c.cnvs_msgcount,
        c.cnvs_created,
        c.cnvs_updated,
        c.cnvs_dept,
        c.cnvs_contact_reason,
        c.cnvs_occurrence,
        c.cnvs_software,
        c.cnvs_rating_agent,
        c.cnvs_rating_nps,
        c.cnvs_reopened_count,
        c.cnvs_description,
        c.cnvs_tax_id,
        ct.cnts_id,
        ct.cnts_name,
        ct.cnts_phone,
        a.agnt_name,
        a.agnt_grp
    FROM conversations c
    LEFT JOIN contacts ct ON ct.cnts_id = c.cnvs_cnts
    LEFT JOIN agents a ON a.agnt_id = c.cnvs_agnt
    ORDER BY c.cnvs_created
"""

UNMAPPED_AGENTS_QUERY = """
    SELECT COUNT(*) FROM conversations
    WHERE cnvs_agnt IS NOT NULL
      AND cnvs_agnt NOT IN (SELECT agnt_id FROM agents)
"""

UNMAPPED_DEPTS_QUERY = """
    SELECT COUNT(*) FROM conversations
    WHERE cnvs_dept IS NULL OR cnvs_dept = 0
"""

FETCH_GROUPS_QUERY = """
    SELECT DISTINCT a.agnt_name, a.agnt_grp
    FROM agents a
    JOIN conversations c ON c.cnvs_agnt = a.agnt_id
    WHERE (c.cnvs_created::timestamp BETWEEN $1::timestamp AND $2::timestamp)
       OR (c.cnvs_updated::timestamp BETWEEN $3::timestamp AND $4::timestamp)
"""

FETCH_GROUPS_QUERY_ALL = """
    SELECT DISTINCT a.agnt_name, a.agnt_grp
    FROM agents a
    JOIN conversations c ON c.cnvs_agnt = a.agnt_id
"""

MESSAGES_BY_CONVERSATION_QUERY = """
    SELECT
        m.msgs_created,
        m.msgs_content,
        m.msgs_direction,
        m.msgs_type,
        a.agnt_name,
        c.cnts_name
    FROM messages m
    JOIN conversations cv ON m.msgs_cnvs = cv.cnvs_id
    JOIN contacts c ON cv.cnvs_cnts = c.cnts_id
    LEFT JOIN agents a ON m.msgs_agnt = a.agnt_id
    WHERE m.msgs_cnvs = $1
      AND m.msgs_type = 'text'
    ORDER BY m.msgs_created ASC
"""

MESSAGES_FOR_CONVERSATIONS_QUERY = """
    SELECT
        m.msgs_cnvs,
        m.msgs_created,
        m.msgs_content,
        m.msgs_direction,
        a.agnt_name,
        ct.cnts_name
    FROM messages m
    JOIN conversations cv ON m.msgs_cnvs = cv.cnvs_id
    JOIN contacts ct ON cv.cnvs_cnts = ct.cnts_id
    LEFT JOIN agents a ON m.msgs_agnt = a.agnt_id
    WHERE m.msgs_cnvs = ANY($1::int[])
      AND m.msgs_type = 'text'
    ORDER BY m.msgs_cnvs, m.msgs_created ASC
"""

AUDITORIA_CONTATOS_QUERY = """
    SELECT c.cnts_id, c.cnts_name, c.cnts_phone, cv.cnvs_id, cv.cnvs_dept,
           cv.cnvs_rating_agent, cv.cnvs_rating_nps, m.msgs_created, a.agnt_name
    FROM contacts c
    JOIN conversations cv ON c.cnts_id = cv.cnvs_cnts
    JOIN messages m ON cv.cnvs_id = m.msgs_cnvs
    LEFT JOIN agents a ON m.msgs_agnt = a.agnt_id
    WHERE m.msgs_created::timestamp BETWEEN $1::timestamp AND $2::timestamp
    ORDER BY c.cnts_id, m.msgs_created ASC
"""

AUDITORIA_CONTATOS_QUERY_ALL = """
    SELECT c.cnts_id, c.cnts_name, c.cnts_phone, cv.cnvs_id, cv.cnvs_dept,
           cv.cnvs_rating_agent, cv.cnvs_rating_nps, m.msgs_created, a.agnt_name
    FROM contacts c
    JOIN conversations cv ON c.cnts_id = cv.cnvs_cnts
    JOIN messages m ON cv.cnvs_id = m.msgs_cnvs
    LEFT JOIN agents a ON m.msgs_agnt = a.agnt_id
    ORDER BY c.cnts_id, m.msgs_created ASC
"""

DEPT_LIST_QUERY = """
    SELECT DISTINCT c.cnvs_dept FROM conversations c
    WHERE (c.cnvs_created::timestamp BETWEEN $1::timestamp AND $2::timestamp)
       OR (c.cnvs_updated::timestamp BETWEEN $3::timestamp AND $4::timestamp)
"""

DEPT_LIST_QUERY_ALL = """
    SELECT DISTINCT c.cnvs_dept FROM conversations c
"""

# ── Conversation list / detail queries ───────────────────────────────

CONVERSATION_LIST_QUERY = f"""
    SELECT
        c.cnvs_id,
        c.cnvs_created,
        c.cnvs_updated,
        c.cnvs_status,
        c.cnvs_dept,
        c.cnvs_rating_agent,
        c.cnvs_rating_nps,
        c.cnvs_msgcount,
        c.cnvs_reopened_count,
        c.cnvs_channel,
        ct.cnts_id,
        ct.cnts_name,
        ct.cnts_phone,
        a.agnt_name,
        a.agnt_grp,
        CASE
            WHEN first_resp.sent_at IS NOT NULL
             AND last_client.client_at IS NOT NULL
             AND first_resp.sent_at > last_client.client_at
            THEN ROUND(
                LEAST(
                    EXTRACT(EPOCH FROM (first_resp.sent_at - last_client.client_at)) / 60.0,
                    {MAX_ART_MINUTES}.0
                ),
                1
            )::numeric
            ELSE NULL
        END AS cnvs_art_minutes
    FROM conversations c
    LEFT JOIN contacts ct ON ct.cnts_id = c.cnvs_cnts
    LEFT JOIN agents a ON a.agnt_id = c.cnvs_agnt
    LEFT JOIN LATERAL (
        SELECT MIN(m.msgs_created) AS sent_at
        FROM messages m
        LEFT JOIN agents a_resp ON a_resp.agnt_id = m.msgs_agnt
        WHERE m.msgs_cnvs = c.cnvs_id
          AND m.msgs_direction = 'sent'
          AND m.msgs_agnt IS NOT NULL
          AND a_resp.agnt_grp IS NOT NULL
    ) first_resp ON true
    LEFT JOIN LATERAL (
        SELECT MAX(m.msgs_created) AS client_at
        FROM messages m
        WHERE m.msgs_cnvs = c.cnvs_id
          AND m.msgs_direction = 'received'
          AND (first_resp.sent_at IS NULL OR (
              m.msgs_created < first_resp.sent_at
              AND m.msgs_created >= first_resp.sent_at - INTERVAL '24 hours'
          ))
    ) last_client ON true
    WHERE 1=1
"""

CONVERSATION_LIST_COUNT = """
    SELECT COUNT(*) FROM conversations c
    LEFT JOIN contacts ct ON ct.cnts_id = c.cnvs_cnts
    LEFT JOIN agents a ON a.agnt_id = c.cnvs_agnt
    WHERE 1=1
"""

CONVERSATION_DETAIL_QUERY = """
    SELECT
        c.cnvs_id,
        c.cnvs_created,
        c.cnvs_updated,
        c.cnvs_status,
        c.cnvs_dept,
        c.cnvs_rating_agent,
        c.cnvs_rating_nps,
        c.cnvs_contact_reason,
        c.cnvs_occurrence,
        c.cnvs_msgcount,
        c.cnvs_reopened_count,
        c.cnvs_channel,
        c.cnvs_description,
        c.cnvs_bird,
        c.cnvs_tax_id,
        c.cnvs_software,
        ct.cnts_id,
        ct.cnts_name,
        ct.cnts_phone,
        a.agnt_name
    FROM conversations c
    LEFT JOIN contacts ct ON ct.cnts_id = c.cnvs_cnts
    LEFT JOIN agents a ON a.agnt_id = c.cnvs_agnt
    WHERE c.cnvs_id = $1
"""

CONVERSATION_EXPORT_IDS = """
    SELECT c.cnvs_id FROM conversations c
    LEFT JOIN contacts ct ON ct.cnts_id = c.cnvs_cnts
    LEFT JOIN agents a ON a.agnt_id = c.cnvs_agnt
    WHERE 1=1
"""

CONVERSATION_EXPORT_DETAILS = """
    SELECT
        c.cnvs_id,
        c.cnvs_created,
        c.cnvs_updated,
        c.cnvs_status,
        c.cnvs_dept,
        c.cnvs_rating_agent,
        c.cnvs_rating_nps,
        c.cnvs_contact_reason,
        c.cnvs_occurrence,
        c.cnvs_msgcount,
        c.cnvs_reopened_count,
        c.cnvs_channel,
        c.cnvs_description,
        c.cnvs_bird,
        c.cnvs_tax_id,
        c.cnvs_software,
        ct.cnts_id,
        ct.cnts_name,
        ct.cnts_phone,
        a.agnt_name
    FROM conversations c
    LEFT JOIN contacts ct ON ct.cnts_id = c.cnvs_cnts
    LEFT JOIN agents a ON a.agnt_id = c.cnvs_agnt
    WHERE c.cnvs_id = ANY($1)
"""

# ── Materialized View queries (fast dashboard) ───────────────────────

SURVEY_MV_RANGE = """
    SELECT * FROM vw_survey_data
    WHERE cnvs_created::timestamp BETWEEN $1::timestamp AND $2::timestamp
    ORDER BY cnvs_id, msgs_created ASC
"""

SURVEY_MV_ALL = """
    SELECT * FROM vw_survey_data
    ORDER BY cnvs_id, msgs_created ASC
"""

REFRESH_MV = "REFRESH MATERIALIZED VIEW CONCURRENTLY vw_survey_data"
