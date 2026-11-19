-- Usernames use SQLite's default BINARY collation: comparison is case-sensitive (R1).
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('admin', 'user'))
);

-- Server-side sessions: the cookie holds only the random token, so logout can invalidate it (R6.1).
-- Times are Unix seconds; last_seen_at drives the idle timeout (R8).
CREATE TABLE IF NOT EXISTS sessions (
    token        TEXT    PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at   REAL    NOT NULL,
    last_seen_at REAL    NOT NULL
);
