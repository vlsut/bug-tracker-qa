# Decision log

Short records of project decisions: what was decided and why.
Newest at the bottom. A changed decision gets a new entry that refers to the old one.

## D-001 · System under test: own Bug Tracker app
**Decision:** Test a small Bug Tracker web app (Flask + SQLite) built inside this repository,
not a public demo site.
**Why:** Full control over UI, API and the database, so tests can verify data at all three levels.
Public demo sites give no database access.

## D-002 · Environment and dependencies: uv
**Decision:** uv manages Python, the virtual environment and dependencies (`pyproject.toml`, `uv.lock`,
`.python-version`). No `pip`, no manual venv.
**Why:** One command (`uv sync`) reproduces the exact environment locally and in CI; fast installs;
locked versions.

## D-003 · Test stack
**Decision:** pytest as the runner; Playwright (pytest-playwright) for UI; requests for API;
sqlite3 for DB checks; ruff for lint and format; pytest-html for reports; GitHub Actions for CI.
**Why:** Widely used, Python-native tools; one runner for all test levels.

## D-004 · Excel report vs database
**Decision:** The app exports a bug report to Excel; an E2E test downloads it and compares every cell
with the database. `NULL`, `""` and `"-"` are treated as the same "empty" value.
**Why:** Reconciling generated reports against source data is a common and costly check in real
business applications; automating it shows data-level testing beyond UI clicks.

## D-005 · Reading Excel: openpyxl, not pandas
**Decision:** Read the report with openpyxl.
**Why:** The check is cell-by-cell, so values must be read exactly as stored. pandas reads `.xlsx`
through openpyxl anyway and by default converts values (empty → `NaN`, `1` → `1.0`, drops leading
zeros), which can hide real differences or create false failures.

## D-006 · Mobile web via emulation; no native app
**Decision:** Test the responsive web app on emulated devices with Playwright device descriptors
(iPhone on WebKit, Pixel on Chromium, iPad). Native mobile app testing (Appium) is out of scope.
**Why:** Same framework and Page Objects, low cost, covers layout and touch behaviour.
Native testing needs a separate app and stack and would dilute this project.
**Limit:** Emulation is not a real device; real-device coverage is not claimed.

## D-007 · Way of working with the AI agent
**Decision:** The QA lead defines what to test (test cases, data, expected DB values) and approves
every change; the AI agent (Claude Code) implements and runs tests. Rules for the agent live in
`CLAUDE.md`.
**Why:** Mirrors how AI-assisted test automation is done in practice: the human owns test design
and the bug-vs-test-error decision, the agent owns implementation.

## D-008 · Tests run against a live server started by a fixture
**Decision:** A session-scoped pytest fixture starts the Flask app as a real HTTP server
(werkzeug `make_server` in a background thread, free port chosen by the OS). If `BT_BASE_URL` is
set, tests use that already running app instead.
**Why:** Playwright needs a real URL, so UI, API and mobile tests all hit the same running app
over HTTP rather than Flask's test client. Binding the socket before the thread starts means
no sleeps or readiness polling; a free port avoids clashes (e.g. AirPlay on 5000).
