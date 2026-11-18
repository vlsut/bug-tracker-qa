"""Shared fixtures: live app server and API client."""

import threading
from collections.abc import Iterator

import pytest
from werkzeug.serving import make_server

import config
from api import ApiClient
from app import create_app


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    """Base URL of a live app server, started once per test session.

    A real HTTP server (not Flask's test client) is used so that UI, API and mobile
    tests all exercise the same running app. Overrides pytest-playwright's
    ``base_url`` fixture, so ``page.goto("/")`` works too.
    """
    if config.BASE_URL:
        yield config.BASE_URL
        return

    # make_server binds the socket before returning, so the server accepts
    # connections as soon as the thread starts — no readiness polling needed.
    server = make_server(config.HOST, config.PORT, create_app(), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{config.HOST}:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture
def api_client(base_url: str) -> Iterator[ApiClient]:
    """API client bound to the live server."""
    client = ApiClient(base_url)
    yield client
    client.close()
