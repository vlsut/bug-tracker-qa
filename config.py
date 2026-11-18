"""Settings for the app and the tests, read from environment variables with defaults."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

HOST: str = os.getenv("BT_HOST", "127.0.0.1")
# 0 lets the OS pick a free port, so parallel or repeated runs never collide.
PORT: int = int(os.getenv("BT_PORT", "0"))
# When set, tests run against an already running app instead of starting their own.
BASE_URL: str | None = os.getenv("BT_BASE_URL") or None
DB_PATH: Path = Path(os.getenv("BT_DB_PATH", str(PROJECT_ROOT / "bug_tracker.db")))
HEADLESS: bool = os.getenv("BT_HEADLESS", "true").lower() in {"1", "true", "yes"}
REQUEST_TIMEOUT: float = float(os.getenv("BT_REQUEST_TIMEOUT", "10"))
