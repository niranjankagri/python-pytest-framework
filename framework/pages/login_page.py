"""The login page of the Notes app."""

from playwright.sync_api import Page

from framework.config import Settings


class LoginPage:
    """Login form: email, password, submit, and the messages it shows."""

    def __init__(self, page: Page, settings: Settings) -> None:
        self.page = page
        self.url = f"{settings.app_url}/login"
        # Locators: the app gives every control a data-testid, the most stable choice
        self.email = page.get_by_test_id("login-email")
        self.password = page.get_by_test_id("login-password")
        self.submit = page.get_by_test_id("login-submit")
        # Message of a failed login (wrong email or password)
        self.alert = page.get_by_test_id("alert-message")
        # "is required" hints under empty fields (Bootstrap form validation)
        self.field_errors = page.locator(".invalid-feedback")

    def open(self) -> "LoginPage":
        self.page.goto(self.url)
        return self

    def login(self, email: str, password: str) -> None:
        """Fills the form and submits it; the caller checks where the app went."""
        self.email.fill(email)
        self.password.fill(password)
        self.submit.click()
