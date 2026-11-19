"""Parser for docs/test-cases.md (D-021)."""

from pathlib import Path

import pytest

from tools.case_parser import TestCaseFormatError, parse, split_steps

pytestmark = pytest.mark.tooling

VALID_CASE = """\
### TC-DEMO-001 · Demo case
- **Priority:** High · **Level:** UI · **Markers:** `ui`, `smoke` · **Covers:** R1, R4.2
- **Preconditions:** user `tester` exists.
- **Steps:** 1. Open `/login`. 2. Click "Log in".
- **Expected:** stays on `/login`.
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "test-cases.md"
    path.write_text("# Test cases\n\n## Demo\n\n" + text, encoding="utf-8")
    return path


def test_real_document_parses_into_all_test_cases() -> None:
    cases = parse()

    assert [case.id for case in cases] == [f"TC-LOGIN-{n:03d}" for n in range(1, 15)]
    first = cases[0]
    assert first.summary == "TC-LOGIN-001 · Successful login (user)"
    assert (first.priority, first.level, first.requirements) == ("High", "UI", ["R1", "R2"])
    assert first.markers == ["ui", "smoke"]
    assert len(first.steps) == 3


def test_valid_case_is_read_field_by_field(tmp_path: Path) -> None:
    (case,) = parse(write(tmp_path, VALID_CASE))

    assert case.id == "TC-DEMO-001"
    assert case.title == "Demo case"
    assert case.requirements == ["R1", "R4.2"]
    assert case.preconditions == "user `tester` exists."
    assert case.steps == ["Open `/login`.", 'Click "Log in".']
    assert case.expected == "stays on `/login`."


def test_template_heading_is_not_a_test_case(tmp_path: Path) -> None:
    template = "### TC-<AREA>-NNN · <Short behaviour>\n- **Priority:** High | Low\n\n"

    assert [case.id for case in parse(write(tmp_path, template + VALID_CASE))] == ["TC-DEMO-001"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("1. Open. 2. Click.", ["Open.", "Click."], id="numbered"),
        pytest.param(
            "same as TC-LOGIN-001 on mobile.", ["same as TC-LOGIN-001 on mobile."], id="free-text"
        ),
        pytest.param("1. Request `/bugs`.", ["Request `/bugs`."], id="single-numbered"),
        pytest.param(
            "2. Out of order. 1. First.", ["2. Out of order. 1. First."], id="not-from-one"
        ),
    ],
)
def test_steps_are_split_only_when_numbered_from_one(text: str, expected: list[str]) -> None:
    assert split_steps(text) == expected


@pytest.mark.parametrize(
    ("change", "message"),
    [
        pytest.param(
            ("- **Expected:**", "- **Outcome:**"), "unknown field 'Outcome'", id="unknown-field"
        ),
        pytest.param(
            ("- **Expected:** stays on `/login`.\n", ""), "missing Expected", id="missing-expected"
        ),
        pytest.param(("- **Steps:**", "- **Steps**"), "not a field line", id="malformed-line"),
        pytest.param(
            ("**Priority:** High", "**Priority:** Urgent"), "priority 'Urgent'", id="bad-priority"
        ),
        pytest.param(
            ("Covers:** R1, R4.2", "Covers:** R1, X9"), "bad requirement IDs", id="bad-requirement"
        ),
        pytest.param(
            (" · **Markers:** `ui`, `smoke`", ""), "summary line needs exactly", id="missing-part"
        ),
    ],
)
def test_format_errors_name_the_case_and_line(
    tmp_path: Path, change: tuple[str, str], message: str
) -> None:
    broken = VALID_CASE.replace(*change)

    with pytest.raises(TestCaseFormatError, match="TC-DEMO-001") as error:
        parse(write(tmp_path, broken))
    assert message in str(error.value)


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(TestCaseFormatError, match="duplicate test case IDs: TC-DEMO-001"):
        parse(write(tmp_path, VALID_CASE + "\n" + VALID_CASE))
