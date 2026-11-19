"""Login on emulated mobile devices (R9). Emulation only: not real-device coverage."""

import re

import pytest
from playwright.sync_api import expect

from config import UserCredentials
from pages import BugsPage, LoginPage


@pytest.mark.mobile
@pytest.mark.req("R9", "R1", "R2")
@pytest.mark.tc("TC-LOGIN-010")
def test_login_works_on_mobile_without_horizontal_scroll(
    mobile_login_page: LoginPage, regular_user: UserCredentials
) -> None:
    page = mobile_login_page.open().page

    expect(mobile_login_page.form).to_be_in_viewport(ratio=1)
    has_horizontal_scroll = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not has_horizontal_scroll, "the login page scrolls horizontally"

    mobile_login_page.login_as(regular_user)

    expect(page).to_have_url(re.compile(r"/bugs$"))
    expect(BugsPage(page).current_user).to_have_text(regular_user.username)
