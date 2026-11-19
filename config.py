"""Settings for the app and the tests, read from environment variables with defaults."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent

# Local runs read .env; real environment variables (e.g. GitHub Secrets in CI) take precedence.
load_dotenv(PROJECT_ROOT / ".env", override=False)

HOST: str = os.getenv("BT_HOST", "127.0.0.1")
# 0 lets the OS pick a free port, so parallel or repeated runs never collide.
PORT: int = int(os.getenv("BT_PORT", "0"))
# When set, tests run against an already running app instead of starting their own.
BASE_URL: str | None = os.getenv("BT_BASE_URL") or None
DB_PATH: Path = Path(os.getenv("BT_DB_PATH", str(PROJECT_ROOT / "bug_tracker.db")))
HEADLESS: bool = os.getenv("BT_HEADLESS", "true").lower() in {"1", "true", "yes"}
REQUEST_TIMEOUT: float = float(os.getenv("BT_REQUEST_TIMEOUT", "10"))
# R8: idle timeout in seconds; configurable so it can be changed without code changes.
SESSION_IDLE_TIMEOUT: int = int(os.getenv("BT_SESSION_IDLE_TIMEOUT", "1800"))
# Emulated devices for mobile tests: Playwright device descriptor names. Each descriptor picks
# its own browser (iPhone and iPad: WebKit, Pixel: Chromium). Comma-separated override.
MOBILE_DEVICES: tuple[str, ...] = tuple(
    name.strip()
    for name in os.getenv("BT_MOBILE_DEVICES", "iPhone 15,Pixel 7,iPad (gen 7)").split(",")
    if name.strip()
)


class MissingSettingError(RuntimeError):
    """A required environment variable is not set."""


@dataclass(frozen=True)
class UserCredentials:
    """Login data of a test user.

    The password is masked in ``repr`` so it never shows up in assertion messages,
    pytest reports or logs. Pass this object around instead of the raw password.
    """

    username: str
    password: str
    role: str

    def __repr__(self) -> str:
        return f"UserCredentials(username={self.username!r}, password='***', role={self.role!r})"


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        # Names the variable, never a value.
        raise MissingSettingError(
            f"{name} is not set. Locally: copy .env.example to .env and fill it in. "
            "In CI: add it as a GitHub Secret."
        )
    return value


def admin_user() -> UserCredentials:
    """Test user with the admin role, from TEST_ADMIN_USERNAME / TEST_ADMIN_PASSWORD."""
    return UserCredentials(
        username=_require("TEST_ADMIN_USERNAME"),
        password=_require("TEST_ADMIN_PASSWORD"),
        role="admin",
    )


def regular_user() -> UserCredentials:
    """Test user with the user role, from TEST_USER_USERNAME / TEST_USER_PASSWORD."""
    return UserCredentials(
        username=_require("TEST_USER_USERNAME"),
        password=_require("TEST_USER_PASSWORD"),
        role="user",
    )


@dataclass(frozen=True)
class JiraSettings:
    """Connection to Jira for the test-case export (D-020).

    The API token is masked in ``repr`` so it never reaches logs, output or error messages.
    """

    base_url: str
    email: str
    api_token: str
    project_key: str
    issue_type: str

    def __repr__(self) -> str:
        return (
            f"JiraSettings(base_url={self.base_url!r}, email={self.email!r}, api_token='***', "
            f"project_key={self.project_key!r}, issue_type={self.issue_type!r})"
        )


def jira_settings() -> JiraSettings:
    """Jira settings from JIRA_* variables; JIRA_ISSUE_TYPE defaults to "Task"."""
    return JiraSettings(
        base_url=_require("JIRA_BASE_URL").rstrip("/"),
        email=_require("JIRA_EMAIL"),
        api_token=_require("JIRA_API_TOKEN"),
        project_key=_require("JIRA_PROJECT_KEY"),
        issue_type=os.getenv("JIRA_ISSUE_TYPE") or "Task",
    )
