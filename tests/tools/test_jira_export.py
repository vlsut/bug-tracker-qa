"""Jira export against an in-memory fake of the Jira REST API — no real Jira calls (D-020)."""

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest

from config import JiraSettings
from tools.case_parser import TestCase, parse
from tools.jira_client import JiraClient, JiraError
from tools.jira_export import Report, export, format_report, issue_fields

pytestmark = pytest.mark.tooling

TOKEN = "fake-token-must-never-appear"
SETTINGS = JiraSettings("https://example.atlassian.net", "qa@example.com", TOKEN, "BTC", "Task")

CASES_MD = """\
### TC-DEMO-001 · First case
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R1, R2
- **Preconditions:** user `tester` exists.
- **Steps:** 1. Open `/login`. 2. Click "Log in".
- **Expected:** redirected to `/bugs`.
- **DB check:** `SELECT COUNT(*) FROM sessions` returns 1.

### TC-DEMO-002 · Second case
- **Priority:** Low · **Level:** API · **Markers:** `api` · **Covers:** R3
- **Steps:** send the form directly.
- **Expected:** stays on `/login`.
- **Note:** a note.
"""


class FakeResponse:
    """Just enough of requests.Response for JiraClient."""

    def __init__(self, status_code: int, body: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._body = body
        self.ok = status_code < 400
        self.content = b"" if body is None else json.dumps(body).encode()
        self.text = self.content.decode()
        self.reason = "Error" if not self.ok else "OK"

    def json(self) -> dict[str, Any]:
        if self._body is None:
            raise ValueError("no body")
        return self._body


class FakeJira:
    """In-memory Jira project: search by label, create, update. Records every call."""

    def __init__(self) -> None:
        self.issues: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, str]] = []
        self.fail_with: int | None = None

    def add(self, summary: str, labels: list[str]) -> str:
        key = f"BTC-{len(self.issues) + 100}"
        self.issues[key] = {"key": key, "fields": {"summary": summary, "labels": labels}}
        return key

    # Mirrors requests.Session.request, whose keyword arguments are untyped.
    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:  # noqa: ANN401
        path = url.removeprefix(SETTINGS.base_url)
        self.calls.append((method, path))
        if self.fail_with:
            return FakeResponse(self.fail_with, {"errorMessages": ["Unauthorized"], "errors": {}})
        if method == "GET" and path == "/rest/api/3/search/jql":
            label = re.search(r'labels = "([^"]+)"', kwargs["params"]["jql"])[1]
            found = [i for i in self.issues.values() if label in i["fields"].get("labels", [])]
            return FakeResponse(200, {"issues": copy.deepcopy(found), "isLast": True})
        if method == "POST" and path == "/rest/api/3/issue":
            key = f"BTC-{len(self.issues) + 1}"
            self.issues[key] = {"key": key, "fields": self._stored(kwargs["json"]["fields"])}
            return FakeResponse(201, {"key": key})
        if method == "PUT" and path.startswith("/rest/api/3/issue/"):
            key = path.rsplit("/", 1)[1]
            self.issues[key]["fields"].update(self._stored(kwargs["json"]["fields"]))
            return FakeResponse(204)
        return FakeResponse(404, {"errorMessages": [f"unexpected {method} {path}"]})

    @staticmethod
    def _stored(fields: dict[str, Any]) -> dict[str, Any]:
        """Like Jira, store a normalised copy (extra ADF attrs), so exact comparison would fail."""
        stored = copy.deepcopy(fields)
        stored.pop("project", None)
        for node in stored.get("description", {}).get("content", []):
            if node["type"] == "orderedList":
                node["attrs"] = {"order": 1}
        return stored

    def writes(self) -> list[tuple[str, str]]:
        return [call for call in self.calls if call[0] != "GET"]


@pytest.fixture
def jira() -> FakeJira:
    return FakeJira()


@pytest.fixture
def client(jira: FakeJira) -> JiraClient:
    return JiraClient(SETTINGS, session=jira)


def cases_from(tmp_path: Path, text: str = CASES_MD) -> list[TestCase]:
    path = tmp_path / "test-cases.md"
    path.write_text(text, encoding="utf-8")
    return parse(path)


def run(tmp_path: Path, client: JiraClient, dry_run: bool = False, text: str = CASES_MD) -> Report:
    return export(cases_from(tmp_path, text), client, SETTINGS, dry_run=dry_run)


def test_first_run_creates_one_issue_per_test_case(
    tmp_path: Path, jira: FakeJira, client: JiraClient
) -> None:
    report = run(tmp_path, client)

    assert [a.kind for a in report.actions] == ["create", "create"]
    first = next(
        i["fields"] for i in jira.issues.values() if "TC-DEMO-001" in i["fields"]["labels"]
    )
    assert first["summary"] == "TC-DEMO-001 · First case"
    assert first["labels"] == ["R1", "R2", "TC-DEMO-001", "test-case"]
    assert first["priority"] == {"name": "High"}
    assert first["issuetype"] == {"name": "Task"}


def test_second_run_changes_nothing_and_creates_no_duplicates(
    tmp_path: Path, jira: FakeJira, client: JiraClient
) -> None:
    run(tmp_path, client)
    writes_after_first_run = len(jira.writes())

    report = run(tmp_path, client)

    assert [a.kind for a in report.actions] == ["unchanged", "unchanged"]
    assert len(jira.writes()) == writes_after_first_run
    assert len(jira.issues) == 2


def test_changed_test_case_updates_only_its_issue(
    tmp_path: Path, jira: FakeJira, client: JiraClient
) -> None:
    run(tmp_path, client)

    report = run(tmp_path, client, text=CASES_MD.replace("stays on `/login`.", "shows an error."))

    kinds = {a.case.id: (a.kind, a.changes) for a in report.actions}
    assert kinds == {
        "TC-DEMO-001": ("unchanged", []),
        "TC-DEMO-002": ("update", ["description"]),
    }
    assert len(jira.issues) == 2


def test_update_keeps_labels_added_in_jira(
    tmp_path: Path, jira: FakeJira, client: JiraClient
) -> None:
    run(tmp_path, client)
    key = next(k for k, i in jira.issues.items() if "TC-DEMO-002" in i["fields"]["labels"])
    jira.issues[key]["fields"]["labels"].append("regression")

    run(tmp_path, client, text=CASES_MD.replace("Covers:** R3", "Covers:** R4"))

    assert jira.issues[key]["fields"]["labels"] == ["R4", "TC-DEMO-002", "regression", "test-case"]


def test_several_issues_with_one_id_are_reported_and_not_written(
    tmp_path: Path, jira: FakeJira, client: JiraClient
) -> None:
    jira.add("copy 1", ["TC-DEMO-001", "test-case"])
    jira.add("copy 2", ["TC-DEMO-001", "test-case"])

    report = run(tmp_path, client)

    error = next(a for a in report.actions if a.case.id == "TC-DEMO-001")
    assert error.kind == "error"
    assert "BTC-100, BTC-101" in error.message
    assert report.failed
    assert all("TC-DEMO-001" not in str(call) for call in jira.writes())


def test_dry_run_only_reads(tmp_path: Path, jira: FakeJira, client: JiraClient) -> None:
    report = run(tmp_path, client, dry_run=True)

    assert [a.kind for a in report.actions] == ["create", "create"]
    assert jira.writes() == []
    assert jira.issues == {}
    assert "would create" in format_report(report, SETTINGS, dry_run=True)


def test_issues_missing_from_docs_are_reported_not_deleted(
    tmp_path: Path, jira: FakeJira, client: JiraClient
) -> None:
    orphan = jira.add("TC-DEMO-099 · Removed case", ["TC-DEMO-099", "test-case"])

    report = run(tmp_path, client)

    assert report.orphans == [(orphan, "TC-DEMO-099 · Removed case")]
    assert orphan in jira.issues
    assert all(method != "DELETE" for method, _ in jira.calls)


def test_description_has_numbered_steps_and_inline_code(tmp_path: Path) -> None:
    case = cases_from(tmp_path)[0]

    content = issue_fields(case, SETTINGS)["description"]["content"]

    steps = next(node for node in content if node["type"] == "orderedList")
    assert len(steps["content"]) == 2
    code = [n for n in json.dumps(content).split('"marks"') if '"code"' in n]
    assert code, "backticked text should be inline code"
    assert "Source fingerprint: " in json.dumps(content)


def test_db_check_follows_the_expected_result(tmp_path: Path) -> None:
    with_check, without_check = cases_from(tmp_path)

    def headings(case: TestCase) -> list[str]:
        content = issue_fields(case, SETTINGS)["description"]["content"]
        return [n["content"][0]["text"] for n in content if n["type"] == "heading"]

    assert headings(with_check)[-2:] == ["Expected result", "DB check"]
    assert "DB check" not in headings(without_check)


def test_token_never_appears_in_output_or_errors(
    tmp_path: Path, jira: FakeJira, client: JiraClient
) -> None:
    jira.fail_with = 401

    report = run(tmp_path, client)
    output = format_report(report, SETTINGS, dry_run=False)

    assert report.failed
    assert "HTTP 401: Unauthorized" in output
    assert TOKEN not in output
    assert TOKEN not in repr(SETTINGS)
    with pytest.raises(JiraError) as error:
        client.issues_with_label("TC-DEMO-001")
    assert TOKEN not in str(error.value)
