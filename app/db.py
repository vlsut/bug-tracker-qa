"""SQLite access for the app: one connection per request, schema setup."""

import sqlite3
from pathlib import Path

from flask import Flask, current_app, g

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a connection with rows accessible by column name and foreign keys enforced."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_db() -> sqlite3.Connection:
    """Connection for the current request, opened on first use."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_error: BaseException | None = None) -> None:
    """Close the request's connection, if one was opened."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_schema(db_path: Path) -> None:
    """Create missing tables; existing tables and data are kept."""
    with connect(db_path) as connection:
        connection.executescript(SCHEMA_PATH.read_text())
    connection.close()


def init_app(app: Flask) -> None:
    """Register connection teardown with the app."""
    app.teardown_appcontext(close_db)
