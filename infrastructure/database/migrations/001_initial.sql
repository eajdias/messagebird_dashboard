-- ============================================================
-- Migration 001: Initial Schema (PostgreSQL)
-- ============================================================

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    cnts_id SERIAL PRIMARY KEY,
    cnts_name VARCHAR(255),
    cnts_phone VARCHAR(50),
    cnts_bird VARCHAR(255) UNIQUE NOT NULL,
    cnts_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cnts_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cnts_custom1 VARCHAR(255),
    cnts_custom2 VARCHAR(255),
    cnts_custom3 VARCHAR(255),
    cnts_custom4 VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_contacts_bird ON contacts(cnts_bird);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(cnts_phone);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    agnt_id SERIAL PRIMARY KEY,
    agnt_name VARCHAR(255),
    agnt_bird VARCHAR(255) UNIQUE NOT NULL,
    agnt_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agnt_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agnt_grp VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_agents_bird ON agents(agnt_bird);
CREATE INDEX IF NOT EXISTS idx_agents_grp ON agents(agnt_grp);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    cnvs_id SERIAL PRIMARY KEY,
    cnvs_msgcount INTEGER DEFAULT 0,
    cnvs_cnts INTEGER REFERENCES contacts(cnts_id),
    cnvs_agnt INTEGER REFERENCES agents(agnt_id),
    cnvs_status VARCHAR(50),
    cnvs_channel VARCHAR(255),
    cnvs_bird VARCHAR(255) UNIQUE NOT NULL,
    cnvs_created TIMESTAMP,
    cnvs_updated TIMESTAMP,
    cnvs_last TIMESTAMP,
    cnvs_lang INTEGER,
    cnvs_software VARCHAR(255),
    cnvs_tax_id VARCHAR(50),
    cnvs_dept INTEGER,
    cnvs_rating_agent INTEGER,
    cnvs_rating_nps INTEGER,
    cnvs_reopened_count INTEGER DEFAULT 0,
    cnvs_contact_reason INTEGER,
    cnvs_occurrence INTEGER,
    cnvs_description TEXT
);

CREATE INDEX IF NOT EXISTS idx_conversations_bird ON conversations(cnvs_bird);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(cnvs_status);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(cnvs_created);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(cnvs_updated);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    msgs_id SERIAL PRIMARY KEY,
    msgs_cnvs INTEGER NOT NULL REFERENCES conversations(cnvs_id),
    msgs_agnt INTEGER REFERENCES agents(agnt_id),
    msgs_direction VARCHAR(20),
    msgs_status VARCHAR(50),
    msgs_type VARCHAR(50),
    msgs_content TEXT,
    msgs_bird VARCHAR(255) UNIQUE NOT NULL,
    msgs_created TIMESTAMP,
    msgs_updated TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_bird ON messages(msgs_bird);
CREATE INDEX IF NOT EXISTS idx_messages_cnvs ON messages(msgs_cnvs);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(msgs_created);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages(msgs_direction);
CREATE INDEX IF NOT EXISTS idx_messages_cnvs_created ON messages(msgs_cnvs, msgs_created);

-- Sync history table
CREATE TABLE IF NOT EXISTS sync (
    sync_id SERIAL PRIMARY KEY,
    sync_resource VARCHAR(50) NOT NULL,
    sync_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_duration REAL,
    sync_records_count INTEGER,
    sync_cursor VARCHAR(255),
    sync_offset INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sync_resource_created ON sync(sync_resource, sync_created);

-- Sync errors table
CREATE TABLE IF NOT EXISTS sync_errors (
    err_id SERIAL PRIMARY KEY,
    err_resource VARCHAR(50),
    err_code VARCHAR(50),
    err_message TEXT,
    err_context TEXT,
    err_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    err_retry_count INTEGER DEFAULT 0,
    err_resolved_at TIMESTAMP
);
