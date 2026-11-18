# bug-tracker-qa

[![CI](https://github.com/vlsut/bug-tracker-qa/actions/workflows/ci.yml/badge.svg)](https://github.com/vlsut/bug-tracker-qa/actions/workflows/ci.yml)

A small Bug Tracker web app (Flask + SQLite) and an automated test framework for it
at three levels — UI, API and database — plus verification of an Excel report against the
database and mobile web testing on emulated devices.

> Work in progress. Currently: project setup and a `/health` smoke test.

## Stack
Python 3.15, uv, Flask, SQLite, pytest, Playwright, requests, openpyxl, pytest-html, ruff.
Rationale for each choice: [docs/decisions.md](docs/decisions.md).

## Setup
```bash
uv sync
uv run playwright install chromium webkit
```

## Run
```bash
uv run flask --app app run --debug --port 5001   # the app
uv run pytest                                    # all tests, HTML report in reports/
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
docs/       test cases and decision log
```

## License
MIT — see [LICENSE](LICENSE).
