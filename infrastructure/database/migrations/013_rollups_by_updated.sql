-- ============================================================
-- Migration 013: Rollups agregados por cnvs_updated
-- ============================================================
-- Troca a agregação dos rollups de cnvs_created para cnvs_updated,
-- alinhando com o painel de conversas (que filtra por created OR
-- updated). Avaliações/NPS/ART passam a aparecer no bucket do dia
-- em que realmente ocorreram (survey respondido), em vez do dia
-- em que a conversa foi criada.

CREATE INDEX IF NOT EXISTS idx_messages_cnvs_updated ON messages (msgs_cnvs, msgs_created);

-- ── Refresh Function (corrected) ────────────────────────────
-- SLA thresholds are the defaults (60 / 480 minutes), matching
-- domain.constants (SLA_FRT_THRESHOLD_MINUTES / MAX_ART_MINUTES).

CREATE OR REPLACE FUNCTION refresh_stats_rollups()
RETURNS void AS $$
BEGIN
    -- Refresh daily rollup (last 6 months)
    DELETE FROM stats_daily WHERE bucket_day >= CURRENT_DATE - INTERVAL '6 months';
    INSERT INTO stats_daily (
        bucket_day, channel, dept,
        total_conversations, total_messages,
        avg_rating, rated_conversations,
        nps_score, nps_rated_conversations,
        avg_art, art_conversations,
        sla_compliance, returners, unique_contacts
    )
    SELECT
        DATE_TRUNC('day', cv.cnvs_updated)::date AS bucket_day,
        COALESCE(cv.cnvs_channel, 'unknown') AS channel,
        COALESCE(a.agnt_grp, 'N/A') AS dept,
        COUNT(*) AS total_conversations,
        SUM(cv.cnvs_msgcount) AS total_messages,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
        COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
        ROUND(
            (COUNT(CASE WHEN cv.cnvs_rating_nps >= 9 THEN 1 END)
             - COUNT(CASE WHEN cv.cnvs_rating_nps <= 6 THEN 1 END)) * 100.0
            / NULLIF(COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END), 0),
            1
        ) AS nps_score,
        COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated_conversations,
        ROUND(AVG(cv.cnvs_art_minutes), 2) AS avg_art,
        COUNT(CASE WHEN cv.cnvs_art_minutes IS NOT NULL THEN 1 END) AS art_conversations,
        ROUND(
            COUNT(CASE WHEN cv.cnvs_art_minutes > 0 AND cv.cnvs_art_minutes <= 60 THEN 1 END) * 100.0
            / NULLIF(COUNT(CASE WHEN cv.cnvs_art_minutes > 0 AND cv.cnvs_art_minutes <= 480 THEN 1 END), 0),
            2
        ) AS sla_compliance,
        COUNT(CASE WHEN cv.cnvs_reopened_count > 0 THEN 1 END) AS returners,
        COUNT(DISTINCT cv.cnvs_cnts) AS unique_contacts
    FROM conversations cv
    LEFT JOIN agents a ON cv.cnvs_agnt = a.agnt_id
    WHERE cv.cnvs_updated >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('day', cv.cnvs_updated), COALESCE(cv.cnvs_channel, 'unknown'), COALESCE(a.agnt_grp, 'N/A')
    ON CONFLICT (bucket_day, channel, dept) DO UPDATE SET
        total_conversations = EXCLUDED.total_conversations,
        total_messages = EXCLUDED.total_messages,
        avg_rating = EXCLUDED.avg_rating,
        rated_conversations = EXCLUDED.rated_conversations,
        nps_score = EXCLUDED.nps_score,
        nps_rated_conversations = EXCLUDED.nps_rated_conversations,
        avg_art = EXCLUDED.avg_art,
        art_conversations = EXCLUDED.art_conversations,
        sla_compliance = EXCLUDED.sla_compliance,
        returners = EXCLUDED.returners,
        unique_contacts = EXCLUDED.unique_contacts;

    -- Refresh weekly rollup (last 2 years)
    DELETE FROM stats_weekly WHERE bucket_week >= CURRENT_DATE - INTERVAL '2 years';
    INSERT INTO stats_weekly (
        bucket_week, channel, dept,
        total_conversations, total_messages,
        avg_rating, rated_conversations,
        nps_score, nps_rated_conversations,
        avg_art, art_conversations,
        sla_compliance, returners, unique_contacts
    )
    SELECT
        (DATE_TRUNC('week', cv.cnvs_updated))::date AS bucket_week,
        COALESCE(cv.cnvs_channel, 'unknown') AS channel,
        COALESCE(a.agnt_grp, 'N/A') AS dept,
        COUNT(*) AS total_conversations,
        SUM(cv.cnvs_msgcount) AS total_messages,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
        COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
        ROUND(
            (COUNT(CASE WHEN cv.cnvs_rating_nps >= 9 THEN 1 END)
             - COUNT(CASE WHEN cv.cnvs_rating_nps <= 6 THEN 1 END)) * 100.0
            / NULLIF(COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END), 0),
            1
        ) AS nps_score,
        COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated_conversations,
        ROUND(AVG(cv.cnvs_art_minutes), 2) AS avg_art,
        COUNT(CASE WHEN cv.cnvs_art_minutes IS NOT NULL THEN 1 END) AS art_conversations,
        ROUND(
            COUNT(CASE WHEN cv.cnvs_art_minutes > 0 AND cv.cnvs_art_minutes <= 60 THEN 1 END) * 100.0
            / NULLIF(COUNT(CASE WHEN cv.cnvs_art_minutes > 0 AND cv.cnvs_art_minutes <= 480 THEN 1 END), 0),
            2
        ) AS sla_compliance,
        COUNT(CASE WHEN cv.cnvs_reopened_count > 0 THEN 1 END) AS returners,
        COUNT(DISTINCT cv.cnvs_cnts) AS unique_contacts
    FROM conversations cv
    LEFT JOIN agents a ON cv.cnvs_agnt = a.agnt_id
    WHERE cv.cnvs_updated >= CURRENT_DATE - INTERVAL '2 years'
    GROUP BY DATE_TRUNC('week', cv.cnvs_updated), COALESCE(cv.cnvs_channel, 'unknown'), COALESCE(a.agnt_grp, 'N/A')
    ON CONFLICT (bucket_week, channel, dept) DO UPDATE SET
        total_conversations = EXCLUDED.total_conversations,
        total_messages = EXCLUDED.total_messages,
        avg_rating = EXCLUDED.avg_rating,
        rated_conversations = EXCLUDED.rated_conversations,
        nps_score = EXCLUDED.nps_score,
        nps_rated_conversations = EXCLUDED.nps_rated_conversations,
        avg_art = EXCLUDED.avg_art,
        art_conversations = EXCLUDED.art_conversations,
        sla_compliance = EXCLUDED.sla_compliance,
        returners = EXCLUDED.returners,
        unique_contacts = EXCLUDED.unique_contacts;

    -- Refresh monthly rollup (all data)
    DELETE FROM stats_monthly;
    INSERT INTO stats_monthly (
        bucket_month, channel, dept,
        total_conversations, total_messages,
        avg_rating, rated_conversations,
        nps_score, nps_rated_conversations,
        avg_art, art_conversations,
        sla_compliance, returners, unique_contacts
    )
    SELECT
        DATE_TRUNC('month', cv.cnvs_updated)::date AS bucket_month,
        COALESCE(cv.cnvs_channel, 'unknown') AS channel,
        COALESCE(a.agnt_grp, 'N/A') AS dept,
        COUNT(*) AS total_conversations,
        SUM(cv.cnvs_msgcount) AS total_messages,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
        COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
        ROUND(
            (COUNT(CASE WHEN cv.cnvs_rating_nps >= 9 THEN 1 END)
             - COUNT(CASE WHEN cv.cnvs_rating_nps <= 6 THEN 1 END)) * 100.0
            / NULLIF(COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END), 0),
            1
        ) AS nps_score,
        COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated_conversations,
        ROUND(AVG(cv.cnvs_art_minutes), 2) AS avg_art,
        COUNT(CASE WHEN cv.cnvs_art_minutes IS NOT NULL THEN 1 END) AS art_conversations,
        ROUND(
            COUNT(CASE WHEN cv.cnvs_art_minutes > 0 AND cv.cnvs_art_minutes <= 60 THEN 1 END) * 100.0
            / NULLIF(COUNT(CASE WHEN cv.cnvs_art_minutes > 0 AND cv.cnvs_art_minutes <= 480 THEN 1 END), 0),
            2
        ) AS sla_compliance,
        COUNT(CASE WHEN cv.cnvs_reopened_count > 0 THEN 1 END) AS returners,
        COUNT(DISTINCT cv.cnvs_cnts) AS unique_contacts
    FROM conversations cv
    LEFT JOIN agents a ON cv.cnvs_agnt = a.agnt_id
    GROUP BY DATE_TRUNC('month', cv.cnvs_updated), COALESCE(cv.cnvs_channel, 'unknown'), COALESCE(a.agnt_grp, 'N/A')
    ON CONFLICT (bucket_month, channel, dept) DO UPDATE SET
        total_conversations = EXCLUDED.total_conversations,
        total_messages = EXCLUDED.total_messages,
        avg_rating = EXCLUDED.avg_rating,
        rated_conversations = EXCLUDED.rated_conversations,
        nps_score = EXCLUDED.nps_score,
        nps_rated_conversations = EXCLUDED.nps_rated_conversations,
        avg_art = EXCLUDED.avg_art,
        art_conversations = EXCLUDED.art_conversations,
        sla_compliance = EXCLUDED.sla_compliance,
        returners = EXCLUDED.returners,
        unique_contacts = EXCLUDED.unique_contacts;

    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_nps_by_month;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agent_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_channel_distribution;
END;
$$ LANGUAGE plpgsql;
