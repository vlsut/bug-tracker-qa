"""Export the test cases in docs/test-cases.md to Jira, one issue per case (D-020).

Run:  uv run python -m tools.jira_export [--dry-run]

Idempotent: each case is found again by its ID label (e.g. ``TC-LOGIN-001``); a second run
updates changed issues and never creates duplicates. ``--dry-run`` makes read-only lookups and
reports what would be created or updated, without writing anything.
"""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any

import config
from config import JiraSettings
from tools.case_parser import REQUIREMENT_ID, TestCase, TestCaseFormatError, parse
from tools.jira_client import JiraClient, JiraError

TEST_CASE_LABEL = "test-case"
CASE_ID_LABEL = re.compile(r"^TC-[A-Z]+-\d{3}$")
FINGERPRINT = re.compile(r"Source fingerprint: ([0-9a-f]{12})")
# Our priorities map 1:1 onto Jira's default priority names.
JIRA_PRIORITY = {"High": "High", "Medium": "Medium", "Low": "Low"}


@dataclass
class Action:
    """What the export does (or would do) for one test case."""

    kind: str  # create | update | unchanged | error
    case: TestCase
    key: str = ""
    changes: list[str] = field(default_factory=list)
    message: str = ""


@dataclass
class Report:
    """Result of one export run."""

    actions: list[Action] = field(default_factory=list)
    orphans: list[tuple[str, str]] = field(default_factory=list)  # (issue key, summary)

    def count(self, kind: str) -> int:
        """Number of actions of one kind."""
        return sum(action.kind == kind for action in self.actions)

    @property
    def failed(self) -> bool:
        """True if any case could not be exported."""
        return self.count("error") > 0


# --- Issue content ----------------------------------------------------------------------


def is_managed_label(label: str) -> bool:
    """Labels the export owns; any other label set by people in Jira is kept."""
    return label == TEST_CASE_LABEL or bool(
        REQUIREMENT_ID.match(label) or CASE_ID_LABEL.match(label)
    )


def managed_labels(case: TestCase) -> list[str]:
    """``test-case``, the case ID and the requirement IDs it covers."""
    return sorted({TEST_CASE_LABEL, case.id, *case.requirements})


def _inline(text: str) -> list[dict[str, Any]]:
    """Text nodes; `backticked` parts become inline code."""
    nodes = []
    for part in re.split(r"(`[^`]+`)", text):
        if not part:
            continue
        if len(part) > 1 and part.startswith("`") and part.endswith("`"):
            nodes.append({"type": "text", "text": part[1:-1], "marks": [{"type": "code"}]})
        else:
            nodes.append({"type": "text", "text": part})
    return nodes


def _paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": _inline(text)}


def _heading(text: str) -> dict[str, Any]:
    return {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": text}]}


def description_body(case: TestCase) -> list[dict[str, Any]]:
    """Description content in Atlassian Document Format, without the generated footer."""
    markers = ", ".join(case.markers)
    covers = ", ".join(case.requirements)
    summary = f"Priority: {case.priority} · Level: {case.level} · Markers: {markers}"
    body = [_paragraph(f"{summary} · Covers: {covers}")]
    for title, text in (("Preconditions", case.preconditions), ("Data", case.data)):
        if text:
            body += [_heading(title), _paragraph(text)]
    steps = case.steps
    body.append(_heading("Steps"))
    if len(steps) > 1:
        items = [{"type": "listItem", "content": [_paragraph(step)]} for step in steps]
        body.append({"type": "orderedList", "content": items})
    else:
        body.append(_paragraph(steps[0]))
    body += [_heading("Expected result"), _paragraph(case.expected)]
    for title, text in case.extra_fields:
        body += [_heading(title), _paragraph(text)]
    return body


def fingerprint(fields: dict[str, Any]) -> str:
    """Short hash of everything the export writes, to tell changed cases from unchanged ones.

    Jira normalises stored descriptions, so comparing them field by field would report changes
    that are not there; the fingerprint in the footer is compared instead.
    """
    canonical = json.dumps(fields, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def issue_fields(case: TestCase, settings: JiraSettings) -> dict[str, Any]:
    """All fields the export writes for one test case."""
    fields: dict[str, Any] = {
        "summary": case.summary,
        "issuetype": {"name": settings.issue_type},
        "labels": managed_labels(case),
        "priority": {"name": JIRA_PRIORITY[case.priority]},
        "description": {"type": "doc", "version": 1, "content": description_body(case)},
    }
    footer = (
        f"Generated from docs/test-cases.md ({case.id}). Edit the test case there; changes made "
        f"in Jira are overwritten on the next export. Source fingerprint: {fingerprint(fields)}"
    )
    fields["description"]["content"].append(
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": footer, "marks": [{"type": "em"}]}],
        }
    )
    return fields


def _text_of(node: object) -> str:
    """All text inside an ADF node."""
    if isinstance(node, dict):
        return node.get("text", "") + "".join(_text_of(child) for child in node.get("content", []))
    return ""


def changed_fields(existing: dict[str, Any], wanted: dict[str, Any]) -> list[str]:
    """Names of the fields that differ between an issue in Jira and what the export would write."""
    current = existing.get("fields", {})
    changes = []
    if current.get("summary") != wanted["summary"]:
        changes.append("summary")
    if (current.get("issuetype") or {}).get("name") != wanted["issuetype"]["name"]:
        changes.append("issue type")
    if (current.get("priority") or {}).get("name") != wanted["priority"]["name"]:
        changes.append("priority")
    current_managed = sorted(
        label for label in current.get("labels", []) if is_managed_label(label)
    )
    if current_managed != wanted["labels"]:
        changes.append("labels")
    stored = FINGERPRINT.search(_text_of(current.get("description")))
    if stored is None or stored[1] != FINGERPRINT.search(_text_of(wanted["description"]))[1]:
        changes.append("description")
    return changes


# --- Export -----------------------------------------------------------------------------


def export(
    cases: list[TestCase], client: JiraClient, settings: JiraSettings, dry_run: bool
) -> Report:
    """Create or update one issue per test case; in a dry run only read from Jira."""
    report = Report()
    for case in cases:
        wanted = issue_fields(case, settings)
        try:
            found = client.issues_with_label(case.id)
            if len(found) > 1:
                keys = ", ".join(issue["key"] for issue in found)
                report.actions.append(
                    Action("error", case, message=f"{len(found)} issues carry this ID: {keys}")
                )
                continue
            if not found:
                key = "" if dry_run else client.create_issue(wanted)
                report.actions.append(Action("create", case, key=key))
                continue
            issue = found[0]
            changes = changed_fields(issue, wanted)
            if not changes:
                report.actions.append(Action("unchanged", case, key=issue["key"]))
                continue
            if not dry_run:
                # Keep labels people added in Jira; replace only the ones the export owns.
                kept = [
                    lbl for lbl in issue["fields"].get("labels", []) if not is_managed_label(lbl)
                ]
                client.update_issue(
                    issue["key"], {**wanted, "labels": sorted({*kept, *wanted["labels"]})}
                )
            report.actions.append(Action("update", case, key=issue["key"], changes=changes))
        except JiraError as error:
            report.actions.append(Action("error", case, message=str(error)))

    try:
        known = {case.id for case in cases}
        for issue in client.issues_with_label(TEST_CASE_LABEL):
            ids = [lbl for lbl in issue["fields"].get("labels", []) if CASE_ID_LABEL.match(lbl)]
            if not any(case_id in known for case_id in ids):
                report.orphans.append((issue["key"], issue["fields"].get("summary", "")))
    except JiraError as error:
        report.orphans.append(("?", f"orphan check failed: {error}"))
    return report


def format_report(report: Report, settings: JiraSettings, dry_run: bool) -> str:
    """Human-readable result of a run."""
    mode = "DRY RUN — read-only lookups, nothing written" if dry_run else "export"
    lines = [
        f"Jira {mode}: project {settings.project_key}, issue type {settings.issue_type}, "
        f"{len(report.actions)} test cases"
    ]
    for action in report.actions:
        verb = {
            "create": "would create" if dry_run else "created",
            "update": "would update" if dry_run else "updated",
        }.get(action.kind, action.kind)
        key = f" {action.key}" if action.key else ""
        detail = f" ({', '.join(action.changes)})" if action.changes else ""
        detail += f" — {action.message}" if action.message else ""
        lines.append(f"  {verb:<13}{key:<10} {action.case.summary}{detail}")
    if report.orphans:
        lines.append(
            "Orphans (labelled test-case in Jira, not in docs/test-cases.md; not deleted):"
        )
        lines += [f"  {key} {summary}" for key, summary in report.orphans]
    lines.append(
        f"Summary: {report.count('create')} create, {report.count('update')} update, "
        f"{report.count('unchanged')} unchanged, {report.count('error')} errors, "
        f"{len(report.orphans)} orphans"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; exit code 1 on any error."""
    parser = argparse.ArgumentParser(description="Export docs/test-cases.md to Jira.")
    parser.add_argument(
        "--dry-run", action="store_true", help="read-only lookups; show what would change"
    )
    args = parser.parse_args(argv)
    try:
        settings = config.jira_settings()
        cases = parse()
    except (config.MissingSettingError, TestCaseFormatError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    report = export(cases, JiraClient(settings), settings, dry_run=args.dry_run)
    print(format_report(report, settings, dry_run=args.dry_run))
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
