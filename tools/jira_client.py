"""Minimal Jira Cloud REST API v3 client for the test-case export."""

from collections.abc import Iterator
from typing import Any, Protocol

import requests

from config import JiraSettings

ISSUE_FIELDS = "summary,labels,priority,description,issuetype"


class HttpSession(Protocol):
    """The part of ``requests.Session`` the client uses; tests pass a fake."""

    def request(self, method: str, url: str, **kwargs: object) -> requests.Response: ...


class JiraError(RuntimeError):
    """A Jira API call failed. The message has the status and Jira's errors, never credentials."""


class JiraClient:
    """Search, create and update issues in one Jira project."""

    def __init__(
        self, settings: JiraSettings, session: HttpSession | None = None, timeout: float = 30
    ) -> None:
        self.settings = settings
        self.timeout = timeout
        if session is None:
            real = requests.Session()
            real.auth = (settings.email, settings.api_token)
            real.headers.update({"Accept": "application/json"})
            session = real
        self.session = session

    def _call(self, method: str, path: str, **kwargs: object) -> dict[str, Any]:
        url = f"{self.settings.base_url}{path}"
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if not response.ok:
            raise JiraError(f"{method} {path} -> HTTP {response.status_code}: {_errors(response)}")
        return response.json() if response.content else {}

    def search(self, jql: str) -> Iterator[dict[str, Any]]:
        """All issues matching the JQL, following pagination."""
        token: str | None = None
        while True:
            params: dict[str, Any] = {"jql": jql, "fields": ISSUE_FIELDS, "maxResults": 100}
            if token:
                params["nextPageToken"] = token
            page = self._call("GET", "/rest/api/3/search/jql", params=params)
            yield from page.get("issues", [])
            token = page.get("nextPageToken")
            if page.get("isLast", True) or not token:
                return

    def issues_with_label(self, label: str) -> list[dict[str, Any]]:
        """Issues of the configured project that carry the label (exact match)."""
        jql = f'project = "{self.settings.project_key}" AND labels = "{label}" ORDER BY key'
        return list(self.search(jql))

    def create_issue(self, fields: dict[str, Any]) -> str:
        """Create an issue in the configured project and return its key."""
        payload = {"fields": {"project": {"key": self.settings.project_key}, **fields}}
        return str(self._call("POST", "/rest/api/3/issue", json=payload)["key"])

    def update_issue(self, key: str, fields: dict[str, Any]) -> None:
        """Replace the given fields of an issue."""
        self._call("PUT", f"/rest/api/3/issue/{key}", json={"fields": fields})


def _errors(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:300] or response.reason
    messages = list(body.get("errorMessages", [])) + [
        f"{name}: {text}" for name, text in body.get("errors", {}).items()
    ]
    return "; ".join(messages) or response.reason
