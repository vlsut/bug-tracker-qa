"""All SQL queries used by tests live here."""

import sqlite3
import time
from pathlib import Path

from app import users
from config import UserCredentials


class DbManager:
    """Direct access to the app's SQLite database for test setup and DB-level checks."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def reset(self) -> None:
        """Delete all data; the schema stays."""
        with self._connect() as connection:
            connection.execute("DELETE FROM sessions")
            connection.execute("DELETE FROM users")
        connection.close()

    def create_user(self, account: UserCredentials) -> None:
        """Create a user through the app's own code path, so the password is hashed as in prod."""
        connection = self._connect()
        try:
            users.create_user(connection, account.username, account.password, account.role)
        finally:
            connection.close()

    def stored_password(self, username: str) -> str | None:
        """Password value as stored in the users table, or None if there is no such user."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
        connection.close()
        return None if row is None else row["password_hash"]

    def session_count(self) -> int:
        """Number of sessions on the server."""
        with self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        connection.close()
        return int(count)

    def set_session_idle(self, token: str, seconds: float) -> None:
        """Make the session look idle for ``seconds`` by moving its last activity into the past.

        Lets expiry tests run without waiting (D-016).
        """
        with self._connect() as connection:
            updated = connection.execute(
                "UPDATE sessions SET last_seen_at = ? WHERE token = ?",
                (time.time() - seconds, token),
            ).rowcount
        connection.close()
        if updated != 1:
            raise LookupError("No session with the given token.")
