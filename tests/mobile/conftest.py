"""Fixtures for mobile web tests on emulated devices (D-006)."""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Browser, Page, Playwright

import config
from pages import LoginPage
from utils.db_manager import DbManager


@pytest.fixture(scope="session")
def mobile_browsers(
    playwright: Playwright, browser_type_launch_args: dict[str, Any]
) -> Iterator[dict[str, Browser]]:
    """One browser per engine, launched on first use and shared by all devices."""
    browsers: dict[str, Browser] = {}
    yield browsers
    for browser in browsers.values():
        browser.close()


@pytest.fixture(params=config.MOBILE_DEVICES)
def mobile_page(
    request: pytest.FixtureRequest,
    playwright: Playwright,
    mobile_browsers: dict[str, Browser],
    browser_type_launch_args: dict[str, Any],
    base_url: str,
) -> Iterator[Page]:
    """Page in a fresh context emulating one device from ``config.MOBILE_DEVICES``."""
    descriptor = dict(playwright.devices[request.param])
    engine = descriptor.pop("default_browser_type")
    if engine not in mobile_browsers:
        mobile_browsers[engine] = playwright[engine].launch(**browser_type_launch_args)
    context = mobile_browsers[engine].new_context(**descriptor, base_url=base_url)
    # Same failure artifacts as pytest-playwright gives its own pages: screenshot + trace.
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    yield page
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        out = _failure_dir(request)
        page.screenshot(path=out / "test-failed-1.png", full_page=True)
        context.tracing.stop(path=out / "trace.zip")
    else:
        context.tracing.stop()
    context.close()


def _failure_dir(request: pytest.FixtureRequest) -> Path:
    """test-results/<test id>/, next to pytest-playwright's own failure output."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", request.node.nodeid).strip("-")
    path = Path(request.config.getoption("--output")) / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def mobile_login_page(mobile_page: Page, clean_db: DbManager) -> LoginPage:
    """Login page object on an emulated device and a freshly reset database."""
    return LoginPage(mobile_page)
