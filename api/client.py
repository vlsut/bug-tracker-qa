"""Thin wrapper over requests so tests never build raw URLs."""

from urllib.parse import urlparse

import requests

import config
from config import UserCredentials

SESSION_COOKIE = "bt_session"


class ApiClient:
    """HTTP client bound to the app's base URL; keeps cookies like a browser."""

    def __init__(self, base_url: str, timeout: float = config.REQUEST_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def get(self, path: str, **kwargs: object) -> requests.Response:
        """Send a GET request to a path relative to the base URL; redirects are followed."""
        return self.session.get(self._url(path), timeout=self.timeout, **kwargs)

    def post(self, path: str, **kwargs: object) -> requests.Response:
        """Send a POST request to a path relative to the base URL; redirects are followed."""
        return self.session.post(self._url(path), timeout=self.timeout, **kwargs)

    def health(self) -> requests.Response:
        """Call the liveness endpoint."""
        return self.get("/health")

    def login(self, account: UserCredentials) -> requests.Response:
        """Submit the login form as the given user."""
        return self.submit_login_form(account.username, account.password)

    def submit_login_form(self, username: str, password: str) -> requests.Response:
        """Submit the login form with raw values, bypassing browser validation.

        Only for non-secret test input (empty, whitespace); use ``login`` for real users.
        """
        return self.post("/login", data={"username": username, "password": password})

    def logout(self) -> requests.Response:
        """Log out the current session."""
        return self.post("/logout")

    @property
    def session_token(self) -> str | None:
        """Value of the session cookie, if the client has one."""
        return self.session.cookies.get(SESSION_COOKIE)

    def use_session_token(self, token: str) -> None:
        """Send requests with this session cookie (e.g. one saved before logout)."""
        host = urlparse(self.base_url).hostname or ""
        self.session.cookies.set(SESSION_COOKIE, token, domain=host, path="/")

    @staticmethod
    def path_of(response: requests.Response) -> str:
        """Path of the page a response ended on, after redirects."""
        return urlparse(response.url).path

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()
