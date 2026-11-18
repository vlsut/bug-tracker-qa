"""Smoke check that the app is up."""

import pytest

from api import ApiClient


@pytest.mark.smoke
@pytest.mark.api
def test_health_endpoint_returns_ok(api_client: ApiClient) -> None:
    response = api_client.health()

    assert response.status_code == 200
    assert response.text == "OK"
