"""Login page."""

from playwright.sync_api import Locator, Page

from config import UserCredentials


class LoginPage:
    """The /login page: form, error messages, login action."""

    PATH = "/login"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.form: Locator = page.get_by_test_id("login-form")
        self.username_input: Locator = page.get_by_label("Username")
        self.password_input: Locator = page.get_by_label("Password")
        self.submit_button: Locator = page.get_by_role("button", name="Log in")
        self.error_message: Locator = page.get_by_test_id("login-error")

    def open(self) -> LoginPage:
        """Go to the login page."""
        self.page.goto(self.PATH)
        return self

    def field_error(self, field: str) -> Locator:
        """Server-side message for one field: ``username`` or ``password``."""
        return self.page.get_by_test_id(f"{field}-error")

    def login_as(self, account: UserCredentials) -> None:
        """Fill in the user's credentials and submit."""
        self.submit(account.username, account.password)

    def submit(self, username: str, password: str) -> None:
        """Fill in the form with the given values (may be empty) and click "Log in"."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()
