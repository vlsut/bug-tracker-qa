"""Server-side sessions with an idle timeout (R6, R8)."""

import secrets
import sqlite3
import time


def create(connection: sqlite3.Connection, user_id: int) -> str:
    """Start a session for the user and return its token."""
    token = secrets.token_urlsafe(32)
    now = time.time()
    connection.execute(
        "INSERT INTO sessions (token, user_id, created_at, last_seen_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now, now),
    )
    connection.commit()
    return token


def resolve(connection: sqlite3.Connection, token: str, idle_timeout: float) -> sqlite3.Row | None:
    """User of an active session, or None.

    An expired session is deleted, so the request is treated as anonymous (R8).
    A valid one has its last activity moved to now (idle, not absolute, timeout).
    """
    row = connection.execute(
        "SELECT s.last_seen_at, u.id, u.username, u.role "
        "FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    now = time.time()
    if now - row["last_seen_at"] > idle_timeout:
        delete(connection, token)
        return None
    connection.execute("UPDATE sessions SET last_seen_at = ? WHERE token = ?", (now, token))
    connection.commit()
    return row


def delete(connection: sqlite3.Connection, token: str) -> None:
    """End the session on the server (R6.1)."""
    connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
    connection.commit()
