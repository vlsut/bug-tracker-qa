"""Shared fixtures (app server, database, users, clients, pages) and traceability checks."""

import re
import threading
from collections.abc import Iterator
from dataclasses import replace
from html import escape
from pathlib import Path

import pytest
from playwright.sync_api import Page
from werkzeug.serving import make_server

import config
from api import ApiClient
from app import create_app, db
from config import UserCredentials
from pages import BugsPage, LoginPage
from utils.db_manager import DbManager

REQUIREMENTS_DOC = config.PROJECT_ROOT / "docs" / "requirements.md"
TEST_CASES_DOC = config.PROJECT_ROOT / "docs" / "test-cases.md"


# --- App and database -------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Database the app under test uses: a fresh temporary file, or the external app's DB."""
    path = config.DB_PATH if config.BASE_URL else tmp_path_factory.mktemp("db") / "bug_tracker.db"
    db.init_schema(path)
    return path


@pytest.fixture(scope="session")
def base_url(db_path: Path) -> Iterator[str]:
    """Base URL of a live app server, started once per test session (D-008).

    Overrides pytest-playwright's ``base_url`` fixture, so ``page.goto("/login")`` works.
    """
    if config.BASE_URL:
        yield config.BASE_URL
        return

    app = create_app({"DATABASE": db_path})
    # make_server binds the socket before returning, so the server accepts
    # connections as soon as the thread starts — no readiness polling needed.
    server = make_server(config.HOST, config.PORT, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{config.HOST}:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture(scope="session")
def db_manager(db_path: Path) -> DbManager:
    """SQL helpers bound to the app's database."""
    return DbManager(db_path)


@pytest.fixture
def clean_db(db_manager: DbManager) -> DbManager:
    """Empty database with the two test users, created fresh for each test."""
    db_manager.reset()
    db_manager.create_user(config.admin_user())
    db_manager.create_user(config.regular_user())
    return db_manager


# --- Test users (passwords stay inside UserCredentials, whose repr masks them) ----------


@pytest.fixture
def admin_user(clean_db: DbManager) -> UserCredentials:
    """The admin test user; exists in a freshly reset database."""
    return config.admin_user()


@pytest.fixture
def regular_user(clean_db: DbManager) -> UserCredentials:
    """The test user with the "user" role; exists in a freshly reset database."""
    return config.regular_user()


@pytest.fixture
def same_password_user(regular_user: UserCredentials, clean_db: DbManager) -> UserCredentials:
    """A second user with the same password as ``regular_user`` (for R7)."""
    account = replace(regular_user, username=f"{regular_user.username}_twin")
    clean_db.create_user(account)
    return account


# --- Clients and pages ------------------------------------------------------------------


@pytest.fixture
def api_client(base_url: str) -> Iterator[ApiClient]:
    """API client bound to the live server, with its own cookie jar."""
    client = ApiClient(base_url)
    yield client
    client.close()


@pytest.fixture
def login_page(page: Page, clean_db: DbManager) -> LoginPage:
    """Login page object on a fresh browser page and a freshly reset database."""
    return LoginPage(page)


@pytest.fixture
def bugs_page(page: Page) -> BugsPage:
    """Bug list page object on the same browser page."""
    return BugsPage(page)


# --- Traceability: every test names the requirements it covers (D-012) ------------------


def _ids_in(doc: Path, pattern: str) -> set[str]:
    return set(re.findall(pattern, doc.read_text(encoding="utf-8")))


def _marker_args(item: pytest.Item, name: str) -> list[str]:
    return [str(arg) for mark in item.iter_markers(name) for arg in mark.args]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Fail collection if a test lacks ``req``, or refers to IDs that are not in the docs."""
    known_reqs = _ids_in(REQUIREMENTS_DOC, r"\bR\d+(?:\.\d+)?\b")
    known_tcs = _ids_in(TEST_CASES_DOC, r"\bTC-[A-Z]+-\d{3}\b")
    problems = []
    for item in items:
        reqs = _marker_args(item, "req")
        if not reqs:
            problems.append(f"{item.nodeid}: no @pytest.mark.req(...)")
        problems += [f"{item.nodeid}: unknown requirement {r}" for r in reqs if r not in known_reqs]
        tcs = _marker_args(item, "tc")
        problems += [f"{item.nodeid}: unknown test case {t}" for t in tcs if t not in known_tcs]
    if problems:
        raise pytest.UsageError("Traceability check failed:\n  " + "\n  ".join(problems))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Iterator[None]:
    """Copy the test case and requirement IDs onto the report for the HTML columns."""
    outcome = yield
    report = outcome.get_result()
    report.test_cases = ", ".join(_marker_args(item, "tc"))
    report.requirements = ", ".join(_marker_args(item, "req"))


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells: list[str]) -> None:
    """Add "Test case" and "Requirements" columns after the test name."""
    cells.insert(2, "<th>Test case</th>")
    cells.insert(3, "<th>Requirements</th>")


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report: pytest.TestReport, cells: list[str]) -> None:
    """Fill the "Test case" and "Requirements" columns."""
    cells.insert(2, f"<td>{escape(getattr(report, 'test_cases', ''))}</td>")
    cells.insert(3, f"<td>{escape(getattr(report, 'requirements', ''))}</td>")
