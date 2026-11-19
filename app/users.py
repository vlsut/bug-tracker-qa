"""User accounts and password hashing (R7)."""

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

ROLES = ("admin", "user")


def hash_password(password: str) -> str:
    """Hash with Werkzeug's default scheme: scrypt with a random salt per call (R7)."""
    return generate_password_hash(password)


def create_user(connection: sqlite3.Connection, username: str, password: str, role: str) -> int:
    """Insert a user with a hashed password and return its id."""
    if role not in ROLES:
        raise ValueError(f"Unknown role {role!r}; expected one of {ROLES}.")
    cursor = connection.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, hash_password(password), role),
    )
    connection.commit()
    return int(cursor.lastrowid or 0)


def find_by_username(connection: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    """User row with exactly this username (case-sensitive, not trimmed), or None."""
    return connection.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def authenticate(
    connection: sqlite3.Connection, username: str, password: str
) -> sqlite3.Row | None:
    """User row if username and password match, otherwise None."""
    user = find_by_username(connection, username)
    if user is None or not check_password_hash(user["password_hash"], password):
        return None
    return user
