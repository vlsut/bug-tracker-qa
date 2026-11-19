"""Access control and logout through the browser (R2, R5, R6)."""

import re

import pytest
from playwright.sync_api import expect

from config import UserCredentials
from pages import BugsPage, LoginPage

LOGIN_URL = re.compile(r"/login$")
BUGS_URL = re.compile(r"/bugs$")


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.req("R5", "R2")
@pytest.mark.tc("TC-LOGIN-007")
def test_anonymous_user_is_redirected_to_login(
    login_page: LoginPage, bugs_page: BugsPage, regular_user: UserCredentials
) -> None:
    bugs_page.open()

    expect(bugs_page.page).to_have_url(LOGIN_URL)
    expect(bugs_page.bug_list).to_have_count(0)

    login_page.login_as(regular_user)

    expect(bugs_page.page).to_have_url(BUGS_URL)
    expect(bugs_page.bug_list).to_be_visible()


@pytest.mark.ui
@pytest.mark.req("R5")
@pytest.mark.tc("TC-LOGIN-007")
def test_health_is_available_without_login(login_page: LoginPage) -> None:
    response = login_page.page.goto("/health")

    assert response is not None and response.ok
    expect(login_page.page).to_have_url(re.compile(r"/health$"))


@pytest.mark.ui
@pytest.mark.req("R6", "R6.2")
@pytest.mark.tc("TC-LOGIN-008")
def test_logout_ends_access_to_protected_pages(
    login_page: LoginPage, bugs_page: BugsPage, regular_user: UserCredentials
) -> None:
    login_page.open().login_as(regular_user)
    expect(bugs_page.bug_list).to_be_visible()

    bugs_page.logout()
    expect(bugs_page.page).to_have_url(LOGIN_URL)

    bugs_page.open()
    expect(bugs_page.page).to_have_url(LOGIN_URL)
    expect(bugs_page.bug_list).to_have_count(0)

    # Step 3 of the test case: Back.
    bugs_page.page.go_back()
    expect(bugs_page.bug_list).to_have_count(0)
    # One more Back reaches the /bugs entry seen before logout — the case R6.2 is about.
    # Limit: Playwright's Chromium and WebKit reload pages on Back instead of showing a cached
    # copy, so this passes even without the app's Cache-Control: no-store (checked by removing
    # it). It confirms the behaviour but does not catch that regression.
    bugs_page.page.go_back()
    expect(bugs_page.page).to_have_url(LOGIN_URL)
    expect(bugs_page.bug_list).to_have_count(0)
