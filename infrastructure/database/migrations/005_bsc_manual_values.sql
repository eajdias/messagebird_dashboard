CREATE TABLE IF NOT EXISTS bsc_manual_values (
    id SERIAL PRIMARY KEY,
    department TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    value DECIMAL NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(department, agent_name, metric_name, period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_bsc_manual_lookup
    ON bsc_manual_values (department, period_start, period_end);
