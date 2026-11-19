"""Bug list page, with the header shared by all authenticated pages."""

from playwright.sync_api import Locator, Page


class BugsPage:
    """The /bugs page: header with the current user and logout, the bug list."""

    PATH = "/bugs"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.current_user: Locator = page.get_by_test_id("current-user")
        self.logout_button: Locator = page.get_by_role("button", name="Log out")
        self.bug_list: Locator = page.get_by_test_id("bug-list")

    def open(self) -> BugsPage:
        """Go to the bug list."""
        self.page.goto(self.PATH)
        return self

    def logout(self) -> None:
        """Click "Log out" in the header."""
        self.logout_button.click()
