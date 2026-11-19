"""Strict parser for docs/test-cases.md (the source of the test cases, D-021).

The Markdown format is a contract: an unknown field, a missing required field or a malformed
line stops parsing with the case ID and line number, so a format slip is caught in CI instead
of silently exporting a broken case.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import config

TEST_CASES_DOC = config.PROJECT_ROOT / "docs" / "test-cases.md"

HEADING = re.compile(r"^### (TC-[A-Z]+-\d{3}) · (.+)$")
FIELD = re.compile(r"^- \*\*([^*]+?):\*\* ?(.*)$")
SUMMARY_PART = re.compile(r"^\*\*([^*]+?):\*\* (.+)$")
REQUIREMENT_ID = re.compile(r"^R\d+(?:\.\d+)?$")
# "1. Open /login. 2. Enter … 3. Click …": a step number followed by a dot and a space.
STEP_NUMBER = re.compile(r"(?:^|\s)(\d{1,2})\.\s")

PRIORITIES = ("High", "Medium", "Low")
# Free-text fields besides the summary line, in the order they are shown. Anything else is an error.
TEXT_FIELDS = {
    "Preconditions": "preconditions",
    "Data (parametrized)": "data",
    "Steps": "steps_text",
    "Expected": "expected",
    "DB check": "db_check",
    "Note": "note",
    "Also check": "also_check",
    "Why at API level": "why_api_level",
}
REQUIRED_TEXT_FIELDS = ("Steps", "Expected")


class TestCaseFormatError(ValueError):
    """docs/test-cases.md does not follow the agreed format."""

    __test__ = False  # not a pytest test class


@dataclass
class TestCase:
    """One manual test case as written in docs/test-cases.md."""

    __test__ = False  # not a pytest test class

    id: str
    title: str
    line: int
    priority: str = ""
    level: str = ""
    markers: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    preconditions: str = ""
    data: str = ""
    steps_text: str = ""
    expected: str = ""
    db_check: str = ""
    note: str = ""
    also_check: str = ""
    why_api_level: str = ""

    @property
    def summary(self) -> str:
        """Title as used in Jira: "TC-LOGIN-001 · Successful login (user)"."""
        return f"{self.id} · {self.title}"

    @property
    def steps(self) -> list[str]:
        """Numbered steps as a list; free-text steps ("same as TC-…") stay one item."""
        return split_steps(self.steps_text)

    @property
    def extra_fields(self) -> list[tuple[str, str]]:
        """Optional notes, as (label, text), in document order."""
        extras = (
            ("Note", self.note),
            ("Also check", self.also_check),
            ("Why at API level", self.why_api_level),
        )
        return [(label, text) for label, text in extras if text]


def split_steps(text: str) -> list[str]:
    """Split "1. a. 2. b." into ["a.", "b."] if numbered 1, 2, 3…; otherwise return [text]."""
    matches = list(STEP_NUMBER.finditer(text))
    numbers = [int(m.group(1)) for m in matches]
    if not matches or numbers != list(range(1, len(numbers) + 1)) or matches[0].start() != 0:
        return [text]
    bounds = [m.start() for m in matches[1:]] + [len(text)]
    return [text[m.end() : end].strip() for m, end in zip(matches, bounds, strict=True)]


def parse(path: Path = TEST_CASES_DOC) -> list[TestCase]:
    """Read all test cases from the document; raise TestCaseFormatError on any format problem."""
    cases: list[TestCase] = []
    current: TestCase | None = None
    seen_fields: set[str] = set()

    def finish() -> None:
        if current is None:
            return
        missing = [name for name in ("Priority", *REQUIRED_TEXT_FIELDS) if name not in seen_fields]
        if missing:
            raise TestCaseFormatError(
                f"{current.id} (line {current.line}): missing {', '.join(missing)}"
            )
        cases.append(current)

    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.rstrip()
        if heading := HEADING.match(line):
            finish()
            current, seen_fields = TestCase(heading[1], heading[2].strip(), number), set()
            continue
        if line.startswith(("## ", "### ", "---")):
            finish()
            current = None
            continue
        if current is None or not line:
            continue
        match = FIELD.match(line)
        if not match:
            raise TestCaseFormatError(f"{current.id} (line {number}): not a field line: {line!r}")
        name, value = match[1], match[2].strip()
        if name in seen_fields:
            raise TestCaseFormatError(f"{current.id} (line {number}): duplicate field {name!r}")
        seen_fields.add(name)
        if name == "Priority":
            _parse_summary_line(current, f"**Priority:** {value}", number)
        elif name in TEXT_FIELDS:
            setattr(current, TEXT_FIELDS[name], value)
        else:
            raise TestCaseFormatError(f"{current.id} (line {number}): unknown field {name!r}")
    finish()

    ids = [case.id for case in cases]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        raise TestCaseFormatError(f"duplicate test case IDs: {', '.join(duplicates)}")
    return cases


def _parse_summary_line(case: TestCase, line: str, number: int) -> None:
    """Parse "**Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R1, R2"."""
    parts: dict[str, str] = {}
    for chunk in line.split(" · "):
        match = SUMMARY_PART.match(chunk.strip())
        if not match:
            raise TestCaseFormatError(f"{case.id} (line {number}): malformed part {chunk!r}")
        parts[match[1]] = match[2].strip()
    expected = {"Priority", "Level", "Markers", "Covers"}
    if set(parts) != expected:
        raise TestCaseFormatError(
            f"{case.id} (line {number}): summary line needs exactly {sorted(expected)}, "
            f"got {sorted(parts)}"
        )
    if parts["Priority"] not in PRIORITIES:
        raise TestCaseFormatError(
            f"{case.id} (line {number}): priority {parts['Priority']!r} not in {PRIORITIES}"
        )
    requirements = [r.strip() for r in parts["Covers"].split(",") if r.strip()]
    bad = [r for r in requirements if not REQUIREMENT_ID.match(r)]
    if not requirements or bad:
        raise TestCaseFormatError(f"{case.id} (line {number}): bad requirement IDs {bad or '[]'}")
    case.priority = parts["Priority"]
    case.level = parts["Level"]
    case.markers = [m.strip().strip("`") for m in parts["Markers"].split(",") if m.strip()]
    case.requirements = requirements
