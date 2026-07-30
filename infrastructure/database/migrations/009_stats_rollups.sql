-- ============================================================
-- Migration 009: Stats Rollup Tables + Materialized Views
-- ============================================================
-- Pre-aggregated tables for dashboard queries across large date ranges.
-- Reduces query time from millions of rows to ~365 (monthly) or ~72 (monthly) rows.

-- ── Rollup Tables ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS stats_monthly (
    bucket_month DATE NOT NULL,
    channel VARCHAR(255) NOT NULL DEFAULT 'unknown',
    dept VARCHAR(100) NOT NULL DEFAULT 'N/A',
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    avg_rating NUMERIC(5,2),
    rated_conversations INTEGER DEFAULT 0,
    nps_score NUMERIC(5,1),
    nps_rated_conversations INTEGER DEFAULT 0,
    avg_art NUMERIC(10,2),
    art_conversations INTEGER DEFAULT 0,
    sla_compliance NUMERIC(5,2),
    returners INTEGER DEFAULT 0,
    unique_contacts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bucket_month, channel, dept)
);

CREATE TABLE IF NOT EXISTS stats_weekly (
    bucket_week DATE NOT NULL,
    channel VARCHAR(255) NOT NULL DEFAULT 'unknown',
    dept VARCHAR(100) NOT NULL DEFAULT 'N/A',
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    avg_rating NUMERIC(5,2),
    rated_conversations INTEGER DEFAULT 0,
    nps_score NUMERIC(5,1),
    nps_rated_conversations INTEGER DEFAULT 0,
    avg_art NUMERIC(10,2),
    art_conversations INTEGER DEFAULT 0,
    sla_compliance NUMERIC(5,2),
    returners INTEGER DEFAULT 0,
    unique_contacts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bucket_week, channel, dept)
);

CREATE TABLE IF NOT EXISTS stats_daily (
    bucket_day DATE NOT NULL,
    channel VARCHAR(255) NOT NULL DEFAULT 'unknown',
    dept VARCHAR(100) NOT NULL DEFAULT 'N/A',
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    avg_rating NUMERIC(5,2),
    rated_conversations INTEGER DEFAULT 0,
    nps_score NUMERIC(5,1),
    nps_rated_conversations INTEGER DEFAULT 0,
    avg_art NUMERIC(10,2),
    art_conversations INTEGER DEFAULT 0,
    sla_compliance NUMERIC(5,2),
    returners INTEGER DEFAULT 0,
    unique_contacts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bucket_day, channel, dept)
);

-- ── Indexes for Rollup Tables ──────────────────────────────

CREATE INDEX IF NOT EXISTS idx_stats_monthly_channel ON stats_monthly (channel);
CREATE INDEX IF NOT EXISTS idx_stats_monthly_dept ON stats_monthly (dept);
CREATE INDEX IF NOT EXISTS idx_stats_monthly_bucket ON stats_monthly (bucket_month);

CREATE INDEX IF NOT EXISTS idx_stats_weekly_channel ON stats_weekly (channel);
CREATE INDEX IF NOT EXISTS idx_stats_weekly_dept ON stats_weekly (dept);
CREATE INDEX IF NOT EXISTS idx_stats_weekly_bucket ON stats_weekly (bucket_week);

CREATE INDEX IF NOT EXISTS idx_stats_daily_channel ON stats_daily (channel);
CREATE INDEX IF NOT EXISTS idx_stats_daily_dept ON stats_daily (dept);
CREATE INDEX IF NOT EXISTS idx_stats_daily_bucket ON stats_daily (bucket_day);

-- ── Materialized Views ─────────────────────────────────────

-- NPS by month
DROP MATERIALIZED VIEW IF EXISTS mv_nps_by_month;
CREATE MATERIALIZED VIEW mv_nps_by_month AS
SELECT
    DATE_TRUNC('month', cv.cnvs_created) AS bucket_month,
    COALESCE(cv.cnvs_channel, 'unknown') AS channel,
    COALESCE(a.agnt_grp, 'N/A') AS dept,
    COUNT(*) AS total_conversations,
    COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated,
    ROUND(
        (COUNT(CASE WHEN cv.cnvs_rating_nps >= 9 THEN 1 END) * 100.0 /
         NULLIF(COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END), 0)) -
        (COUNT(CASE WHEN cv.cnvs_rating_nps <= 6 THEN 1 END) * 100.0 /
         NULLIF(COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END), 0)),
        1
    ) AS nps_score
FROM conversations cv
LEFT JOIN agents a ON cv.cnvs_agnt = a.agnt_id
GROUP BY DATE_TRUNC('month', cv.cnvs_created), COALESCE(cv.cnvs_channel, 'unknown'), COALESCE(a.agnt_grp, 'N/A');

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_nps_by_month ON mv_nps_by_month (bucket_month, channel, dept);

-- Agent stats by month
DROP MATERIALIZED VIEW IF EXISTS mv_agent_stats;
CREATE MATERIALIZED VIEW mv_agent_stats AS
SELECT
    DATE_TRUNC('month', cv.cnvs_created) AS bucket_month,
    a.agnt_name AS agent_name,
    COALESCE(a.agnt_grp, 'N/A') AS dept,
    COUNT(*) AS total_conversations,
    COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
    ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
    COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated,
    ROUND(AVG(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN cv.cnvs_rating_nps END), 1) AS avg_nps
FROM conversations cv
JOIN agents a ON cv.cnvs_agnt = a.agnt_id
GROUP BY DATE_TRUNC('month', cv.cnvs_created), a.agnt_name, COALESCE(a.agnt_grp, 'N/A');

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_agent_stats ON mv_agent_stats (bucket_month, agent_name, dept);

-- Channel distribution by month
DROP MATERIALIZED VIEW IF EXISTS mv_channel_distribution;
CREATE MATERIALIZED VIEW mv_channel_distribution AS
SELECT
    DATE_TRUNC('month', cv.cnvs_created) AS bucket_month,
    COALESCE(cv.cnvs_channel, 'unknown') AS channel,
    COUNT(*) AS total_conversations,
    COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
    ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
    COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated,
    ROUND(AVG(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN cv.cnvs_rating_nps END), 1) AS avg_nps
FROM conversations cv
GROUP BY DATE_TRUNC('month', cv.cnvs_created), COALESCE(cv.cnvs_channel, 'unknown');

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_channel_distribution ON mv_channel_distribution (bucket_month, channel);

-- ── Refresh Function ───────────────────────────────────────

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
        DATE_TRUNC('day', cv.cnvs_created)::date AS bucket_day,
        COALESCE(cv.cnvs_channel, 'unknown') AS channel,
        COALESCE(a.agnt_grp, 'N/A') AS dept,
        COUNT(*) AS total_conversations,
        SUM(cv.cnvs_msgcount) AS total_messages,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
        COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN cv.cnvs_rating_nps END), 1) AS nps_score,
        COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated_conversations,
        NULL AS avg_art,
        0 AS art_conversations,
        NULL AS sla_compliance,
        0 AS returners,
        COUNT(DISTINCT cv.cnvs_cnts) AS unique_contacts
    FROM conversations cv
    LEFT JOIN agents a ON cv.cnvs_agnt = a.agnt_id
    WHERE cv.cnvs_created >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('day', cv.cnvs_created), COALESCE(cv.cnvs_channel, 'unknown'), COALESCE(a.agnt_grp, 'N/A');

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
        (DATE_TRUNC('week', cv.cnvs_created))::date AS bucket_week,
        COALESCE(cv.cnvs_channel, 'unknown') AS channel,
        COALESCE(a.agnt_grp, 'N/A') AS dept,
        COUNT(*) AS total_conversations,
        SUM(cv.cnvs_msgcount) AS total_messages,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
        COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN cv.cnvs_rating_nps END), 1) AS nps_score,
        COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated_conversations,
        NULL AS avg_art,
        0 AS art_conversations,
        NULL AS sla_compliance,
        0 AS returners,
        COUNT(DISTINCT cv.cnvs_cnts) AS unique_contacts
    FROM conversations cv
    LEFT JOIN agents a ON cv.cnvs_agnt = a.agnt_id
    WHERE cv.cnvs_created >= CURRENT_DATE - INTERVAL '2 years'
    GROUP BY DATE_TRUNC('week', cv.cnvs_created), COALESCE(cv.cnvs_channel, 'unknown'), COALESCE(a.agnt_grp, 'N/A');

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
        DATE_TRUNC('month', cv.cnvs_created)::date AS bucket_month,
        COALESCE(cv.cnvs_channel, 'unknown') AS channel,
        COALESCE(a.agnt_grp, 'N/A') AS dept,
        COUNT(*) AS total_conversations,
        SUM(cv.cnvs_msgcount) AS total_messages,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN cv.cnvs_rating_agent END), 2) AS avg_rating,
        COUNT(CASE WHEN cv.cnvs_rating_agent IS NOT NULL THEN 1 END) AS rated_conversations,
        ROUND(AVG(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN cv.cnvs_rating_nps END), 1) AS nps_score,
        COUNT(CASE WHEN cv.cnvs_rating_nps IS NOT NULL THEN 1 END) AS nps_rated_conversations,
        NULL AS avg_art,
        0 AS art_conversations,
        NULL AS sla_compliance,
        0 AS returners,
        COUNT(DISTINCT cv.cnvs_cnts) AS unique_contacts
    FROM conversations cv
    LEFT JOIN agents a ON cv.cnvs_agnt = a.agnt_id
    GROUP BY DATE_TRUNC('month', cv.cnvs_created), COALESCE(cv.cnvs_channel, 'unknown'), COALESCE(a.agnt_grp, 'N/A');

    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_nps_by_month;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agent_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_channel_distribution;
END;
$$ LANGUAGE plpgsql;
