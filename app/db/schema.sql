-- Database schema for request tracking

CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    callback_url TEXT,
    created_at REAL NOT NULL,
    started_at REAL,
    completed_at REAL,
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    client_ip TEXT
);

CREATE INDEX IF NOT EXISTS idx_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_mode ON requests(mode);
CREATE INDEX IF NOT EXISTS idx_created_at ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_client_ip ON requests(client_ip);
