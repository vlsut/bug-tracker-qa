# bug-tracker-qa

[![CI](https://github.com/vlsut/bug-tracker-qa/actions/workflows/ci.yml/badge.svg)](https://github.com/vlsut/bug-tracker-qa/actions/workflows/ci.yml)

A small Bug Tracker web app (Flask + SQLite) and an automated test framework for it
at three levels — UI, API and database — plus verification of an Excel report against the
database and mobile web testing on emulated devices.

> Work in progress. Done: login and logout (requirements R1–R9, test cases TC-LOGIN-001…013).
> Next: bug list, create / close bug, JSON API, Excel report.
>
> Mobile tests use Playwright device emulation, not real devices.

## Stack
Python 3.15, uv, Flask, SQLite, pytest, Playwright, requests, openpyxl, pytest-html, ruff.
Rationale for each choice: [docs/decisions.md](docs/decisions.md).

## Setup
```bash
uv sync
uv run playwright install chromium webkit
cp .env.example .env    # then fill in the test users' usernames and passwords
uv run flask --app app init-db   # only to run the app by hand; tests use a temporary database
```
Credentials are never committed: locally they come from `.env`, in CI from GitHub Secrets
with the same names (see [docs/decisions.md](docs/decisions.md), D-013).

## Run
```bash
uv run flask --app app run --debug --port 5001   # the app
uv run pytest                                    # all tests; HTML report in reports/, failure screenshots and traces in test-results/
uv run pytest -m smoke                           # one level: ui, api, db, e2e, smoke, mobile
uv run ruff check . && uv run ruff format --check .
```

## Layout
```
app/        Flask app (system under test)
pages/      Page Objects
api/        API client
utils/      SQL helpers, Excel-vs-DB comparison
config.py   settings from environment variables
tests/      ui / api / db / e2e / mobile
docs/       requirements and their review, test cases, decision log
```

## License
MIT — see [LICENSE](LICENSE).
