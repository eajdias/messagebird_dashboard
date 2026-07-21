DROP MATERIALIZED VIEW IF EXISTS vw_survey_data;

CREATE MATERIALIZED VIEW vw_survey_data AS
SELECT
    ca.agnt_name AS conversation_agent_name,
    ma.agnt_name AS message_agent_name,
    ca.agnt_grp  AS agent_group,
    ct.cnts_id,
    ct.cnts_name,
    ct.cnts_phone,
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
LEFT JOIN contacts ct ON cv.cnvs_cnts = ct.cnts_id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vw_survey_data_pk
    ON vw_survey_data (cnvs_id, msgs_id);