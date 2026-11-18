"""Thin wrapper over requests so tests never build raw URLs."""

import requests

import config


class ApiClient:
    """HTTP client bound to the app's base URL."""

    def __init__(self, base_url: str, timeout: float = config.REQUEST_TIMEOUT) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def get(self, path: str, **kwargs: object) -> requests.Response:
        """Send a GET request to a path relative to the base URL."""
        return self.session.get(self._url(path), timeout=self.timeout, **kwargs)

    def health(self) -> requests.Response:
        """Call the liveness endpoint."""
        return self.get("/health")

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()
