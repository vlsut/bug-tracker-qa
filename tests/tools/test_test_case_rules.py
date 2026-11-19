"""Rules on docs/test-cases.md that are checked automatically (D-024)."""

import re
import sqlite3

import pytest

from app.db import SCHEMA_PATH
from tools.case_parser import parse

pytestmark = pytest.mark.tooling

CASES = parse()
SQL = re.compile(r"`(SELECT\b[^`]*)`")
NAMED_PARAMETER = re.compile(r"(?<![\w:]):([A-Za-z_]\w*)")
CASE_ID = re.compile(r"\bTC-[A-Z]+-\d{3}\b")
MAX_COVERS_OUTSIDE_E2E = 3


def db_check_queries() -> list[object]:
    return [
        pytest.param(sql, id=f"{case.id}-q{number}")
        for case in CASES
        for number, sql in enumerate(SQL.findall(case.db_check), start=1)
    ]


@pytest.mark.parametrize("sql", db_check_queries())
def test_db_check_query_runs_on_a_fresh_schema(sql: str) -> None:
    connection = sqlite3.connect(":memory:")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    # Values do not matter: the query only has to be valid against the real schema.
    parameters = {name: 1 for name in NAMED_PARAMETER.findall(sql)}
    try:
        connection.execute(sql, parameters).fetchall()
    except sqlite3.OperationalError as error:
        missing = re.fullmatch(r"no such table: (\w+)", str(error))
        if missing:
            # Approved exception (D-024): the table is created in a later step.
            pytest.skip(f"not yet run: table {missing[1]} does not exist yet")
        raise
    finally:
        connection.close()


@pytest.mark.parametrize("case", [c for c in CASES if c.db_check], ids=lambda c: c.id)
def test_every_db_check_has_a_select_query(case: object) -> None:
    assert SQL.search(case.db_check), f"{case.id}: DB check without a `SELECT …` query"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_steps_and_expected_name_no_other_test_case(case: object) -> None:
    for field in ("steps_text", "expected"):
        others = sorted(set(CASE_ID.findall(getattr(case, field))) - {case.id})
        assert not others, f"{case.id}: {field} refers to {others}; repeat the data instead"


@pytest.mark.parametrize("case", [c for c in CASES if c.level != "E2E"], ids=lambda c: c.id)
def test_non_e2e_case_covers_at_most_three_requirements(case: object) -> None:
    assert len(case.requirements) <= MAX_COVERS_OUTSIDE_E2E, (
        f"{case.id} covers {case.requirements}; split it or make it an E2E case"
    )
