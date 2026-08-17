-- 007_users.sql — User management table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'agent',
    name TEXT NOT NULL DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default admin user (password: Zscan@sac123)
-- bcrypt hash for Zscan@sac123
INSERT INTO users (email, password_hash, role, name)
VALUES ('admin@empresa.com', '$2b$12$/vPms2mEw8kIOmdOjvhQ1ugYkUk5PGvbvZYgFcUujLd3bFQ5PhxLy', 'admin', 'Administrador')
ON CONFLICT (email) DO NOTHING;
