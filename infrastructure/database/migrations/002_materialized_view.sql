-- ============================================================
-- Migration 002: Materialized View for Dashboard Queries
-- ============================================================
-- Pre-computes the heavy 4-table JOIN used by all dashboard
-- endpoints. Reduces query time from ~900ms to ~50ms.

DROP MATERIALIZED VIEW IF EXISTS vw_survey_data;

CREATE MATERIALIZED VIEW vw_survey_data AS
SELECT
    ca.agnt_name AS conversation_agent_name,
    ma.agnt_name AS message_agent_name,
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
ORDER BY cv.cnvs_id, m.msgs_created ASC;

-- Unique index for concurrent refresh and efficient range scans
CREATE UNIQUE INDEX IF NOT EXISTS idx_vw_survey_data_pk
    ON vw_survey_data (cnvs_id, msgs_id);

-- Composite indexes for the OR filter pattern used by dashboard queries
CREATE INDEX IF NOT EXISTS idx_vw_survey_created_updated
    ON vw_survey_data (cnvs_created, cnvs_updated);

CREATE INDEX IF NOT EXISTS idx_vw_survey_updated_created
    ON vw_survey_data (cnvs_updated, cnvs_created);
