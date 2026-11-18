"""Bug Tracker web app (system under test)."""

from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    @app.get("/health")
    def health() -> tuple[str, int]:
        """Liveness check used by smoke tests and CI."""
        return "OK", 200

    return app
