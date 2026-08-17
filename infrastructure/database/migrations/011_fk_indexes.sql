-- Migration 011: Foreign key indexes for JOIN performance
-- PostgreSQL does NOT auto-create indexes on FK columns.
-- Every query joining conversations→contacts, conversations→agents needs these.

CREATE INDEX IF NOT EXISTS idx_conversations_cnts ON conversations(cnvs_cnts);
CREATE INDEX IF NOT EXISTS idx_conversations_agnt ON conversations(cnvs_agnt);
