# bug-tracker-qa

[![CI](https://github.com/vlsut/bug-tracker-qa/actions/workflows/ci.yml/badge.svg)](https://github.com/vlsut/bug-tracker-qa/actions/workflows/ci.yml)

A QA showcase: a small Bug Tracker web app (Flask + SQLite), built as the system under test, and
an automated test framework for it at the UI, API and database levels, with mobile web checks on
emulated devices. Every product test traces back to a written requirement, and since the initial
setup every change has gone through a pull request with CI.

**Status:** login and logout — done (requirements, test cases, implementation, automated tests).
Bugs (list, create, close, JSON API) — requirements, review and test cases done; implementation
in progress.

## How I work with AI

Claude Code implements the app and the framework; the QA decisions are mine.

- **Requirements** — I own them: [docs/requirements.md](docs/requirements.md), with stable IDs
  (R1, R4.2, …).
- **Requirements reviews** — done with my own review skill,
  [.claude/skills/wiegers-requirements-checker](.claude/skills/wiegers-requirements-checker/SKILL.md)
  (with its own evals), and saved with my resolutions in
  [docs/requirements-review.md](docs/requirements-review.md).
- **Test design and approval** — [docs/test-cases.md](docs/test-cases.md): every case names the
  requirements it covers; nothing is automated before I approve it.
- **Bug or test bug** — when a test fails, I decide whether the app or the test is wrong; a test is
  never changed just to make it pass.
- **Implementation** — Claude Code works under [CLAUDE.md](CLAUDE.md): rules, coding standards and
  the Feature workflow (spec → review → requirements → test cases → Jira → implementation), with
  STOP points where it waits for my answers or approval.
- **Decisions** — every decision and its reason is in [docs/decisions.md](docs/decisions.md).

## Test management

Test cases are published to Jira, one issue per case, by an idempotent export:
[tools/jira_export.py](tools/jira_export.py). Running it again updates changed issues and never
creates duplicates; `--dry-run` shows what would change without writing anything.

```bash
uv run python -m tools.jira_export --dry-run   # then without --dry-run
```

## What is covered

Automated tests (pytest items; each parametrized row counts):

| Level | Tests | Requirements |
|---|---|---|
| UI (Playwright) | 14 | R1–R6.2 (login, access control, logout) |
| API (requests) | 9 | R4.2, R5, R6.1, R6.2, R8 |
| DB (sqlite3) | 1 | R7 (password storage) |
| Mobile web (emulated iPhone, Pixel, iPad) | 3 | R9, R1, R2 |

Plus automated checks of the test-case documents (format, self-contained cases, DB-check SQL) and
of the Jira export.

Each new test is checked by breaking the behaviour it guards on purpose — the test must fail.

Written and approved test cases: 14 for login (TC-LOGIN, R1–R9) and 54 for bugs (TC-BUG,
R10–R22, not yet automated). Mobile tests use Playwright device emulation, not real devices.

## Stack
Python 3.15, uv, Flask, SQLite, pytest, Playwright, requests, openpyxl, pytest-html, ruff,
GitHub Actions. Rationale for each choice: [docs/decisions.md](docs/decisions.md).

## Setup
```bash
uv sync
uv run playwright install chromium webkit
cp .env.example .env              # then fill in the test users (and Jira, for the export)
uv run flask --app app init-db    # only to run the app by hand; tests use a temporary database
```
Credentials are never committed: locally they come from `.env`, in CI from GitHub Secrets with the
same names.

## Run
```bash
uv run flask --app app run --debug --port 5001   # the app
uv run pytest                                    # all tests; HTML report in reports/
uv run pytest -m api                             # one level: ui, api, db, e2e, smoke, mobile, tooling
uv run ruff check . && uv run ruff format --check .
```
Failed UI tests keep a screenshot and a Playwright trace in `test-results/`.

## Layout
```
app/        Flask app (system under test)
pages/      Page Objects
api/        API client
utils/      SQL helpers, Excel-vs-DB comparison
tools/      test-case parser, Jira export
config.py   settings from environment variables
tests/      ui / api / db / e2e / mobile / tools
docs/       specs, requirements and reviews, test cases, decision log
.claude/    the requirements review skill
```

## Author
Volodymyr Sut, QA Engineer — [LinkedIn](https://www.linkedin.com/in/volodymyr-sut-955671215)

## License
MIT — see [LICENSE](LICENSE).
