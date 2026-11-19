# CLAUDE.md

## Project
A Bug Tracker web app (Flask + SQLite) and an automated test framework for it at three levels:
UI, API, database — plus verification of an Excel report against the database and
mobile web testing (responsive layout on emulated phones and tablets).

- **App:** login, bug list, create / close bug, JSON API `/api/bugs`, bug report exported to Excel.
- **Tests:** pytest + Playwright (UI), requests (API), sqlite3 (DB), openpyxl (Excel report).
- **Environment and dependencies:** uv (see "Tech stack" and "Commands").
- This is a public showcase repository. Everything is built to production-team standards:
  clean architecture, consistent style, green CI, meaningful history.

## Roles
**The user (QA lead) decides:**
- what to test and why: test cases in `docs/test-cases.md`;
- test data and expected results, including expected values in the database;
- whether a failure is a bug in the app or a bug in the test;
- whether a change is accepted. Nothing is committed without the user's OK.

**Claude:** designs and implements the app and the framework, runs tests and linters,
reports results honestly.

## Source of truth
The GitHub repository is the single source of truth for the project. Everything the project
depends on lives here, not in chats:
- `CLAUDE.md` — rules for the agent;
- `docs/specs/<feature>.md` — feature documentation from the user; the input of the
  "Feature workflow".
- `docs/requirements.md` — approved requirements with stable IDs (R1, R4.2, …), open items and
  out-of-scope decisions (owned by the user). Requirements are the basis for test cases.
- `docs/requirements-review.md` — requirements reviews: findings and the owner's resolutions
  that led to the approved requirements. Reviews are done with the project skill
  `.claude/skills/wiegers-requirements-checker/SKILL.md` and saved here, one section per review
  (RR-001, RR-002, …).
- `docs/test-cases.md` — what to test (owned by the user). Every test case refers to the
  requirement IDs it covers; a behaviour without a requirement is not tested until one is added.
- `docs/decisions.md` — decision log: what was decided and why. Read it before proposing changes
  to stack or architecture. When a new decision is made, add an entry (D-00N) in the same commit.
- `README.md` — project overview for people.

## Workflow for every task
1. Read the relevant test case in `docs/test-cases.md`. If it is missing or unclear — ask,
   do not invent requirements.
2. Propose a short plan: files to touch, approach, what will be checked. Wait for OK.
3. Create a branch for the task from an up-to-date `main`, named `<type>/<short-topic>`
   using the Conventional Commits type (e.g. `feat/login-page`, `ci/github-actions`).
4. Implement in small, reviewable increments.
5. Run linters and the relevant tests; show the result (passed / failed, short error).
6. Summarise the change in a few lines and propose a commit message
   (Conventional Commits: `feat:`, `fix:`, `test:`, `refactor:`, `ci:`, `docs:`, `chore:`).
7. Commit only after the user's OK. One logical change per commit.
8. Push the branch, open a pull request, and report the PR link and the CI result.
   The user reviews and merges once CI is green.

**PR checklist** (D-025):
- Every new product test is checked by breaking the behaviour it guards on purpose; the test must
  fail; then the code is restored. The PR description says what was broken and which test failed.
- Every PR that adds or removes product tests updates the "What is covered" table in `README.md`.

## Feature workflow
How a new feature goes from documentation to code. Every step that changes files also follows
"Workflow for every task" (branch, commits, PR). **STOP** means: report, then wait for the user's
answer or approval before doing anything else. Never skip a STOP point.

0. **No documentation yet?** Do not invent it. Get it in one of three ways:
   - the user gives a short description;
   - interview the user with targeted questions: users, inputs, outputs, errors, boundaries,
     permissions;
   - for a feature that already exists: reconstruct the "as-built" behaviour from the code and the
     running app, marking every statement [ASSUMPTION].

   Save the draft in `docs/specs/<feature>.md` and **STOP** for the user's approval before step 1.
1. **Spec.** The feature documentation is in `docs/specs/<feature>.md` — put there by the user,
   or the draft from step 0 once approved.
2. **Review.** Review the spec with the `wiegers-requirements-checker` skill and save the review
   in `docs/requirements-review.md` as a new section (RR-00N).
3. **Clarify.** If the verdict is not Ready: ask the user the review's questions and **STOP**.
   After the answers, add the Resolution section to that review.
4. **Requirements.** Write the approved requirements with IDs into `docs/requirements.md`.
5. **Test cases.** First reconcile with the existing test cases in `docs/test-cases.md`:
   - map each requirement to the existing cases that cover it;
   - flag duplicates and outdated cases (when requirements changed, use the skill's
     Change Impact Review mode);
   - draft only what is missing.

   Keep a reconciliation table: requirement → existing case / new case / outdated case.
   Then write the missing test cases from the requirements into `docs/test-cases.md`. For DB
   checks, put the SELECT query and its expected result in the case's "DB check" field; queries
   may use only the real database schema (`app/schema.sql`).
6. **Self-review**, before showing the test cases to the user. Check each case; items marked
   *(auto)* are also enforced by `tooling` tests (D-024):
   - one check per case; a verifiable expected result; defined test data;
   - not a duplicate of another case; linked to a requirement;
   - **self-contained:** no fixed IDs or counts unless the precondition says only that data
     exists; no data, steps or expected text taken from another case — repeat it
     *(auto: no other TC ID in Steps or Expected)*;
   - **time:** "now" is checked with bounds or a controlled clock; fixed times are inserted;
   - **boundaries:** both sides of every limit and the smallest valid value; non-Latin text and
     emoji wherever a character-counting rule applies; in every layer that enforces the limit;
   - **decision table:** for features with roles and states, a table actor × state (× error
     order) with a case for every cell;
   - **equivalence classes:** every allowed value of a list, in every layer that offers it;
   - **priorities:** High only for core flows, permissions, security and data integrity; give
     the reason if more than about 40 % are High;
   - **lowest sufficient level:** server logic is tested at API level; UI cases only for
     rendering and interaction;
   - **every place user input is shown:** every page and each kind of rendering (page text,
     re-shown form values), and every variant of a page (e.g. open and closed bug);
   - **DB checks** run against the real schema, or are marked "not yet run" with a plan
     *(auto: every DB-check query runs on a fresh schema)*;
   - **"Covers" lists at most 3 requirements** for non-E2E cases *(auto)*.

   Fix what fails, then show the reconciliation table together with the draft test cases and
   **STOP** for the user's approval.
7. **Jira.** After approval, publish the test cases to Jira: run
   `uv run python -m tools.jira_export --dry-run`, show the output, and run it without
   `--dry-run` only after the user's OK (D-020).
8. **Implementation.** Implement the feature and the automated tests from the approved test cases,
   open a PR (following the PR checklist), and **STOP** for the user's review.

## Hard rules
- **Never push to `main` and never merge a pull request.** Every task goes through its own
  branch and PR; merging is the user's decision.
- **Never skip a STOP point** of the "Feature workflow".
- **Never change a test just to make it pass.** If a test fails: stop, show the error, say whether it
  looks like an app bug or a test bug and why. The user decides.
- **Never weaken an assertion** (remove a check, widen an expected value, add a skip/xfail) without
  the user's explicit OK.
- No flaky waits: never use `time.sleep` / `wait_for_timeout` in tests; rely on Playwright
  auto-waiting and web-first assertions (`expect(...)`).
- Do not add tools or libraries that are not listed in "Tech stack" without asking first.
- Do not commit secrets, `.venv/`, `__pycache__/`, `*.db`, test reports, downloaded files.

## Engineering standards
- **Style:** PEP 8, enforced by `ruff check` and `ruff format`. Code must pass both before commit.
- Type hints on all functions; short docstrings for public classes and functions;
  comments explain **why**, not what.
- **Architecture:**
  - Page Object Model for UI; pages expose user actions and locators, assertions live in tests.
  - API client wrapper over `requests` (base URL, auth, JSON helpers) — tests do not build raw URLs.
  - All SQL used by tests lives in `utils/db_manager.py`.
  - Configuration (base URL, DB path, credentials, headless mode) from environment variables
    with sensible defaults in one config module — nothing hardcoded in tests.
- **Locators:** `get_by_role`, `get_by_label`, `get_by_test_id`. Add `data-testid` to the app
  where needed. No long CSS/XPath chains.
- **Test design:**
  - Tests are independent and can run in any order; each creates its own data (via API or DB).
    The database is reset by a fixture.
  - One test checks one behaviour; names describe the behaviour:
    `test_login_with_wrong_password_shows_error`.
  - Use `pytest.mark.parametrize` for data-driven cases; test data lives in fixtures or data files,
    not scattered through tests.
  - pytest markers: `ui`, `api`, `db`, `e2e`, `smoke`, `mobile`, plus `req`/`tc` for traceability and
    `tooling` for tests of internal tools (registered in `pyproject.toml`).
- **Reporting:** HTML report via pytest-html; on UI test failure keep a screenshot and a
  Playwright trace.

## Project structure (target)
```
app/                     Flask app (system under test)
pages/                   Page Objects
api/                     API client
utils/db_manager.py      all SQL queries used by tests
utils/report_compare.py  Excel report vs database comparison
tools/                   internal tools: test-case parser, Jira export (not the app)
config.py                settings from environment variables
tests/ui/  tests/api/  tests/db/  tests/e2e/  tests/mobile/  tests/tools/
tests/conftest.py        fixtures: app server, browser page, API client, clean DB, test users
docs/specs/              feature documentation from the user (one file per feature)
docs/requirements.md     approved requirements (owned by the user)
docs/requirements-review.md  requirements reviews and resolutions
docs/test-cases.md       test cases (owned by the user)
docs/decisions.md        decision log
.github/workflows/       CI: lint + all tests on every push and pull request; report as artifact
```

## Key scenarios
1. **One bug through all three levels:** create a bug in the UI → check it via the API →
   check the row in the database (correct title, status, author). Each level is also tested on its own.
2. **Excel report vs database:** UI → generate the bug report → download Excel → compare
   **every cell** with the database. "Empty" values must be treated as equal: `NULL`, `""` and `"-"`.
   Read cells as they are in the file (openpyxl), without type guessing.
   Mismatches are reported as a clear list: row, column, value in Excel, value in DB.
3. **Mobile web:** the same app on emulated devices via Playwright device descriptors
   (e.g. iPhone on WebKit, Pixel on Chromium, iPad). Check what differs on small screens:
   navigation (burger menu), bug list layout, create-bug form, touch interactions, no horizontal
   scroll. The app must be responsive (mobile-first CSS, viewport meta tag).
   - The device list is defined in one place (config) and tests are parametrized over it —
     never hardcode a device inside a test.
   - Reuse the same Page Objects; add mobile-specific methods only where the UI really differs.
   - Emulation is not a real device: do not claim real-device coverage in README or reports.

## Tech stack
Python (latest), uv, Flask, SQLite (sqlite3), pytest, pytest-playwright, requests, openpyxl,
pytest-html, ruff, GitHub Actions.

- The environment is managed **only with uv**. uv creates and updates `.venv` in the project
  folder automatically; the Python version is pinned in `.python-version` (`uv python pin`).
- Add dependencies with `uv add <package>` / `uv add --dev <package>`; set up a fresh clone with
  `uv sync`. Do not use `pip install`, do not create or activate a venv by hand — run everything
  via `uv run ...`. Commit `pyproject.toml`, `uv.lock` and `.python-version`; never commit `.venv/`.
- Runtime deps: flask, openpyxl (the app writes the report).
  Dev deps: pytest, pytest-playwright, requests, pytest-html, ruff.

## Commands
- Set up: `uv sync` and `uv run playwright install chromium webkit`
- Run the app: `uv run flask --app app run --debug --port 5001` (port 5000 is taken by AirPlay on macOS)
- Run all tests: `uv run pytest`
- Run one level: `uv run pytest -m api` (also `ui`, `db`, `e2e`, `smoke`, `mobile`)
- Lint and format: `uv run ruff check .` and `uv run ruff format .`
- Export test cases to Jira: `uv run python -m tools.jira_export --dry-run` (then without `--dry-run`)
- Run only the tool tests: `uv run pytest -m tooling`

## Language
- Chat: **Russian or English** — reply in the language the user writes in.
- Code, comments, commit messages, README, docs: **English**.
