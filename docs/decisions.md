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

## D-009 · Every task through a branch and a pull request
**Decision:** Each task is done on its own branch (`<type>/<short-topic>`) and lands in `main`
only through a pull request. CI runs on every pull request and on pushes to `main`; the QA lead
merges after CI is green. The agent never pushes to `main` and never merges.
**Why:** `main` stays green and every change is reviewed and tested before it lands — the same
flow a production team uses. Running CI on pull requests plus `main` (not on every branch push)
avoids running the same commit twice.

## D-010 · CI runner pinned to ubuntu-24.04, with job timeouts
**Decision:** CI jobs run on `ubuntu-24.04`, not `ubuntu-latest`. Job timeouts: 10 minutes for
Lint, 20 minutes for Tests.
**Why:** `ubuntu-latest` moved to Ubuntu 26.04. There, `playwright install --with-deps` had to
download ~185 system packages (140 MB) and a slow apt mirror stalled the Tests job for over
10 minutes with no time limit (GitHub's default is 6 hours). A pinned OS makes CI reproducible
and changes it only on purpose; Ubuntu 24.04 is officially supported by Playwright. Timeouts make
a stuck run fail quickly instead of blocking the PR.
**Revisit:** when Playwright officially supports Ubuntu 26.04, or if apt installs stay slow
(option: the official Playwright container image, not adopted for now).

## D-011 · Tests job runs in the official Playwright container
**Decision:** The CI Tests job runs inside `mcr.microsoft.com/playwright/python`, with browsers
and their system libraries preinstalled. The `playwright install --with-deps` step is removed.
Updates D-010: the runner stays pinned to `ubuntu-24.04` and the job timeouts stay; only the
browser setup changes.
**Why:** On both Ubuntu 26.04 and 24.04 runners, the apt install of browser dependencies
(~185 packages, 126–140 MB) stalled for 10+ minutes: the Ubuntu archive mirror served packages
with 40–150 s gaps, so the problem is the mirror, not the OS version. The image removes apt from
CI entirely.
**Trade-off:** The image tag must match the `playwright` version in `uv.lock` (the Python
package only works with browser builds from the same release). They are updated together;
`ci.yml` says so next to the image tag.

## D-012 · Requirements are the basis for test cases
**Decision:** Approved requirements live in `docs/requirements.md` with stable IDs; their reviews
and the owner's resolutions live in `docs/requirements-review.md`. Every test case in
`docs/test-cases.md` names the requirement IDs it covers.
**Why:** Traceability from requirement to test case to automated test: coverage per requirement
is visible, and a failing check can be judged against a stated requirement. Review RR-001 showed
that test cases written without it checked behaviour no requirement stated (DEF-005).
