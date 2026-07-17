
import aiosqlite

SCHEMA = """
-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS contacts (
    cnts_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnts_name TEXT,
    cnts_phone TEXT,
    cnts_bird TEXT UNIQUE NOT NULL,
    cnts_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    cnts_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_contacts_bird ON contacts(cnts_bird);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(cnts_phone);

CREATE TABLE IF NOT EXISTS agents (
    agnt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agnt_name TEXT,
    agnt_bird TEXT UNIQUE NOT NULL,
    agnt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    agnt_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    agnt_grp TEXT
);
CREATE INDEX IF NOT EXISTS idx_agents_bird ON agents(agnt_bird);
CREATE INDEX IF NOT EXISTS idx_agents_grp ON agents(agnt_grp);

CREATE TABLE IF NOT EXISTS conversations (
    cnvs_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnvs_msgcount INTEGER DEFAULT 0,
    cnvs_cnts INTEGER,
    cnvs_agnt INTEGER,
    cnvs_status TEXT,
    cnvs_channel TEXT,
    cnvs_bird TEXT UNIQUE NOT NULL,
    cnvs_created DATETIME,
    cnvs_updated DATETIME,
    cnvs_last DATETIME,
    cnvs_lang INTEGER,
    cnvs_software TEXT,
    cnvs_tax_id TEXT,
    cnvs_dept INTEGER,
    cnvs_rating_agent INTEGER,
    cnvs_rating_nps INTEGER,
    cnvs_reopened_count INTEGER DEFAULT 0,
    cnvs_contact_reason INTEGER,
    cnvs_occurrence INTEGER,
    cnvs_description TEXT,
    FOREIGN KEY (cnvs_cnts) REFERENCES contacts(cnts_id),
    FOREIGN KEY (cnvs_agnt) REFERENCES agents(agnt_id)
);
CREATE INDEX IF NOT EXISTS idx_conversations_bird ON conversations(cnvs_bird);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(cnvs_status);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(cnvs_created);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(cnvs_updated);

CREATE TABLE IF NOT EXISTS messages (
    msgs_id INTEGER PRIMARY KEY AUTOINCREMENT,
    msgs_cnvs INTEGER NOT NULL,
    msgs_agnt INTEGER,
    msgs_direction TEXT,
    msgs_status TEXT,
    msgs_type TEXT,
    msgs_content TEXT,
    msgs_bird TEXT UNIQUE NOT NULL,
    msgs_created DATETIME,
    msgs_updated DATETIME,
    FOREIGN KEY (msgs_cnvs) REFERENCES conversations(cnvs_id),
    FOREIGN KEY (msgs_agnt) REFERENCES agents(agnt_id)
);
CREATE INDEX IF NOT EXISTS idx_messages_bird ON messages(msgs_bird);
CREATE INDEX IF NOT EXISTS idx_messages_cnvs ON messages(msgs_cnvs);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(msgs_created);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages(msgs_direction);
CREATE INDEX IF NOT EXISTS idx_messages_cnvs_created ON messages(msgs_cnvs, msgs_created);
CREATE INDEX IF NOT EXISTS idx_messages_created_direction_cnvs ON messages(msgs_created, msgs_direction, msgs_cnvs);

CREATE TABLE IF NOT EXISTS sync (
    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_resource TEXT NOT NULL,
    sync_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    sync_duration REAL,
    sync_records_count INTEGER,
    sync_cursor TEXT,
    sync_offset INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sync_resource_created ON sync(sync_resource, sync_created);

CREATE TABLE IF NOT EXISTS sync_errors (
    err_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    err_resource  TEXT,
    err_code      TEXT,
    err_message   TEXT,
    err_context   TEXT,
    err_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    err_retry_count INTEGER DEFAULT 0,
    err_resolved_at DATETIME
);

"""

async def init_database(db_path: str):
    """Initializes the database with the required schema."""
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    print(f"Banco de dados inicializado em: {db_path}")

async def run_migrations(db_path: str):
    """Placeholder for future migrations."""
    # (Extract migration logic from m_bird/db.py if needed)
    pass
