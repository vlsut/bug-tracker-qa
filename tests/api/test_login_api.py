"""Login, logout and session lifetime over HTTP, bypassing the browser (R4.2, R5, R6.1, R8)."""

import pytest

import config
from api import ApiClient
from config import UserCredentials
from utils.db_manager import DbManager

# Placeholders replaced inside the test, so real credentials never appear in test IDs.
VALID_USERNAME = object()
VALID_PASSWORD = object()


@pytest.mark.api
@pytest.mark.req("R4.2")
@pytest.mark.tc("TC-LOGIN-011")
@pytest.mark.parametrize(
    ("username", "password", "field"),
    [
        pytest.param("", VALID_PASSWORD, "username", id="empty-username"),
        pytest.param(VALID_USERNAME, "", "password", id="empty-password"),
        pytest.param("   ", VALID_PASSWORD, "username", id="blank-username"),
        pytest.param(VALID_USERNAME, "   ", "password", id="blank-password"),
    ],
)
def test_server_rejects_empty_or_blank_credentials(
    api_client: ApiClient,
    regular_user: UserCredentials,
    db_manager: DbManager,
    username: object,
    password: object,
    field: str,
) -> None:
    response = api_client.submit_login_form(
        regular_user.username if username is VALID_USERNAME else str(username),
        regular_user.password if password is VALID_PASSWORD else str(password),
    )

    assert api_client.path_of(response) == "/login"
    assert f'data-testid="{field}-error"' in response.text
    assert db_manager.session_count() == 0
    assert api_client.path_of(api_client.get("/bugs")) == "/login"


@pytest.mark.api
@pytest.mark.req("R6.1")
@pytest.mark.tc("TC-LOGIN-012")
def test_old_session_cookie_is_rejected_after_logout(
    api_client: ApiClient, regular_user: UserCredentials, base_url: str
) -> None:
    api_client.login(regular_user)
    saved_token = api_client.session_token
    assert saved_token, "login did not set a session cookie"

    api_client.logout()

    replay = ApiClient(base_url)
    try:
        replay.use_session_token(saved_token)
        response = replay.get("/bugs")
    finally:
        replay.close()
    assert replay.path_of(response) == "/login"
    assert 'data-testid="bug-list"' not in response.text


@pytest.mark.api
@pytest.mark.req("R8", "R5")
@pytest.mark.tc("TC-LOGIN-013")
@pytest.mark.parametrize(
    ("idle_seconds", "expected_path"),
    [
        pytest.param(config.SESSION_IDLE_TIMEOUT + 1, "/login", id="expired"),
        # Boundary: just inside the timeout. The 60 s margin absorbs the real clock moving
        # between the update and the request, so the row cannot flake.
        pytest.param(config.SESSION_IDLE_TIMEOUT - 60, "/bugs", id="just-inside"),
    ],
)
def test_session_expires_after_idle_timeout(
    api_client: ApiClient,
    regular_user: UserCredentials,
    db_manager: DbManager,
    idle_seconds: int,
    expected_path: str,
) -> None:
    api_client.login(regular_user)
    assert api_client.session_token, "login did not set a session cookie"

    db_manager.set_session_idle(api_client.session_token, idle_seconds)
    response = api_client.get("/bugs")

    assert api_client.path_of(response) == expected_path
