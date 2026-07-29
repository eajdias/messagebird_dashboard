-- Migration 008: Performance indexes for dashboard queries
-- These indexes improve filtering and sorting on the materialized view.

-- Index for department filtering (agent_group) used by executive and dashboard endpoints
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vw_survey_agent_group
    ON vw_survey_data (agent_group);

-- Covering index for the most common sort pattern: ORDER BY cnvs_id, msgs_created
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vw_survey_created_id
    ON vw_survey_data (cnvs_created, cnvs_id, msgs_created);

-- Index for messages direction filter used in conversation detail queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_direction
    ON messages (msgs_direction) WHERE msgs_direction = 'sent';
