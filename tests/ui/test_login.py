"""Login through the browser (R1–R4.1)."""

import re
from collections.abc import Callable

import pytest
from playwright.sync_api import Page, Request, expect

from config import UserCredentials
from pages import BugsPage, LoginPage
from utils.db_manager import DbManager

# Expected text comes from R3, not from the app's code.
INVALID_LOGIN_MESSAGE = "Invalid username or password"
LOGIN_URL = re.compile(r"/login$")
BUGS_URL = re.compile(r"/bugs$")


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.req("R1", "R2")
@pytest.mark.tc("TC-LOGIN-001")
def test_user_logs_in_and_sees_username(
    login_page: LoginPage, bugs_page: BugsPage, regular_user: UserCredentials
) -> None:
    login_page.open().login_as(regular_user)

    expect(login_page.page).to_have_url(BUGS_URL)
    expect(bugs_page.current_user).to_have_text(regular_user.username)


@pytest.mark.ui
@pytest.mark.req("R1", "R2")
@pytest.mark.tc("TC-LOGIN-002")
def test_admin_logs_in_and_sees_username(
    login_page: LoginPage, bugs_page: BugsPage, admin_user: UserCredentials
) -> None:
    login_page.open().login_as(admin_user)

    expect(login_page.page).to_have_url(BUGS_URL)
    expect(bugs_page.current_user).to_have_text(admin_user.username)


@pytest.mark.ui
@pytest.mark.req("R3")
@pytest.mark.tc("TC-LOGIN-003")
def test_login_with_wrong_password_shows_error(
    login_page: LoginPage, bugs_page: BugsPage, regular_user: UserCredentials
) -> None:
    login_page.open().submit(regular_user.username, "wrong-password")

    expect(login_page.page).to_have_url(LOGIN_URL)
    expect(login_page.error_message).to_have_text(INVALID_LOGIN_MESSAGE)
    bugs_page.open()
    expect(bugs_page.page).to_have_url(LOGIN_URL)


@pytest.mark.ui
@pytest.mark.req("R3")
@pytest.mark.tc("TC-LOGIN-004")
def test_login_with_unknown_username_shows_same_error(
    login_page: LoginPage, regular_user: UserCredentials, db_manager: DbManager
) -> None:
    login_page.open().submit("no_such_user", regular_user.password)

    expect(login_page.page).to_have_url(LOGIN_URL)
    expect(login_page.error_message).to_have_text(INVALID_LOGIN_MESSAGE)
    assert db_manager.session_count() == 0


@pytest.mark.ui
@pytest.mark.req("R4.1")
@pytest.mark.tc("TC-LOGIN-005")
@pytest.mark.parametrize(
    ("fill_username", "fill_password"),
    [
        pytest.param(False, True, id="empty-username"),
        pytest.param(True, False, id="empty-password"),
        pytest.param(False, False, id="both-empty"),
    ],
)
def test_empty_fields_are_marked_and_form_is_not_submitted(
    login_page: LoginPage,
    page: Page,
    regular_user: UserCredentials,
    fill_username: bool,
    fill_password: bool,
) -> None:
    login_page.open()
    login_posts: list[Request] = []
    page.on(
        "request",
        lambda request: login_posts.append(request) if request.method == "POST" else None,
    )

    login_page.submit(
        regular_user.username if fill_username else "",
        regular_user.password if fill_password else "",
    )

    expect(page).to_have_url(LOGIN_URL)
    assert login_posts == [], "the form was submitted to the server"
    for field, filled in (
        (login_page.username_input, fill_username),
        (login_page.password_input, fill_password),
    ):
        expect(field).to_have_attribute("required", "")
        # The browser's own "required" state: True exactly for the fields left empty.
        assert field.evaluate("el => el.validity.valueMissing") is (not filled)


USERNAME_VARIANTS: dict[str, Callable[[str], str]] = {
    "capitalized": str.capitalize,
    "upper-case": str.upper,
    "leading-space": lambda name: f" {name}",
    "trailing-space": lambda name: f"{name} ",
}


@pytest.mark.ui
@pytest.mark.req("R1", "R3")
@pytest.mark.tc("TC-LOGIN-006")
@pytest.mark.parametrize("variant", list(USERNAME_VARIANTS))
def test_username_is_case_sensitive_and_not_trimmed(
    login_page: LoginPage,
    regular_user: UserCredentials,
    db_manager: DbManager,
    variant: str,
) -> None:
    username = USERNAME_VARIANTS[variant](regular_user.username)
    assert username != regular_user.username, "variant must differ from the real username"

    login_page.open().submit(username, regular_user.password)

    expect(login_page.page).to_have_url(LOGIN_URL)
    expect(login_page.error_message).to_have_text(INVALID_LOGIN_MESSAGE)
    assert db_manager.session_count() == 0
