"""Bug Tracker web app (system under test)."""

from pathlib import Path
from typing import Any

import click
from flask import Flask

import config
from app import db, users


def create_app(overrides: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application.

    ``overrides`` replaces settings from ``config`` (tests use it for a temporary database).
    """
    app = Flask(__name__)
    app.config.from_mapping(DATABASE=config.DB_PATH)
    if overrides:
        app.config.update(overrides)

    db.init_app(app)
    app.cli.add_command(init_db_command)

    @app.get("/health")
    def health() -> tuple[str, int]:
        """Liveness check used by smoke tests and CI."""
        return "OK", 200

    return app


def seed_test_users(db_path: Path) -> None:
    """Create the schema and the test users from TEST_* variables, skipping existing users."""
    db.init_schema(db_path)
    connection = db.connect(db_path)
    try:
        for account in (config.admin_user(), config.regular_user()):
            if users.find_by_username(connection, account.username) is None:
                users.create_user(connection, account.username, account.password, account.role)
    finally:
        connection.close()


@click.command("init-db")
def init_db_command() -> None:
    """Create the database schema and the test users (from .env or the environment)."""
    seed_test_users(config.DB_PATH)
    click.echo(f"Database ready: {config.DB_PATH}")
