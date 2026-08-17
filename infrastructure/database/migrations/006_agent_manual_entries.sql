CREATE TABLE IF NOT EXISTS agent_manual_entries (
    id SERIAL PRIMARY KEY,
    department TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    entry_date DATE NOT NULL,
    value DECIMAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(department, agent_name, metric_name, entry_date)
);

CREATE INDEX IF NOT EXISTS idx_agent_manual_lookup
    ON agent_manual_entries (department, agent_name, entry_date);
