"""Fixtures shared by all tests: settings, API clients, throwaway user accounts and browser pages.

Each test that needs a user gets a brand-new account registered through the API, and the
account is deleted afterwards (also when the test failed). So tests never share data, can run
in any order and in parallel, and leave nothing behind on the public demo.
"""

import warnings
from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, Route

from framework.api.notes_client import NotesApiClient
from framework.config import Settings, load_settings
from framework.data.factories import new_user
from framework.pages.login_page import LoginPage
from framework.pages.notes_page import NotesPage


@dataclass
class Account:
    """A registered user. Mutable: a test that changes the password updates it here,
    so the clean-up can still log in and delete the account."""

    name: str
    email: str
    password: str


@pytest.fixture(scope="session")
def settings() -> Settings:
    """URLs and timeouts for the whole run (environment variables or defaults)."""
    return load_settings()


@pytest.fixture
def api_client(settings: Settings) -> Iterator[NotesApiClient]:
    """A client that is not logged in."""
    client = NotesApiClient(settings)
    yield client
    client.close()


def _delete_account(settings: Settings, email: str, password: str) -> None:
    """Logs in with a fresh client and deletes the account; only warns if that is impossible."""
    client = NotesApiClient(settings)
    try:
        if client.login(email, password).status_code == 200:
            client.delete_account()
        else:
            warnings.warn(f"Could not log in to delete test account {email}", stacklevel=2)
    finally:
        client.close()


@pytest.fixture
def account(settings: Settings) -> Iterator[Account]:
    """A freshly registered user, deleted after the test."""
    credentials = new_user()
    client = NotesApiClient(settings)
    response = client.register(credentials.name, credentials.email, credentials.password)
    client.close()
    assert response.status_code == 201, f"Could not register a test user: {response.text}"
    registered = Account(credentials.name, credentials.email, credentials.password)
    yield registered
    _delete_account(settings, registered.email, registered.password)


@pytest.fixture
def second_account(settings: Settings) -> Iterator[Account]:
    """Another registered user, for tests about what one user may see of another's data."""
    credentials = new_user()
    client = NotesApiClient(settings)
    response = client.register(credentials.name, credentials.email, credentials.password)
    client.close()
    assert response.status_code == 201, f"Could not register a second test user: {response.text}"
    registered = Account(credentials.name, credentials.email, credentials.password)
    yield registered
    _delete_account(settings, registered.email, registered.password)


@pytest.fixture
def logged_in_client(settings: Settings, account: Account) -> Iterator[NotesApiClient]:
    """A client logged in as the test's own user."""
    client = NotesApiClient(settings)
    response = client.login(account.email, account.password)
    assert response.status_code == 200, f"Could not log in the test user: {response.text}"
    yield client
    client.close()


@pytest.fixture
def unregistered_cleanup(settings: Settings) -> Iterator[list]:
    """For tests that register users themselves: append (email, password) and they get deleted."""
    created: list[tuple[str, str]] = []
    yield created
    for email, password in created:
        _delete_account(settings, email, password)


# --- browser -------------------------------------------------------------------------------------

# Ad and tracking hosts the demo site loads: blocked, so pages load faster and no ad iframe
# covers a button
BLOCKED_HOSTS = (
    "googlesyndication",
    "doubleclick",
    "google-analytics",
    "googletagmanager",
    "adservice",
    "fundingchoices",
)


def _block_ads(route: Route) -> None:
    if any(host in route.request.url for host in BLOCKED_HOSTS):
        route.abort()
    else:
        route.continue_()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """pytest-playwright hook: every browser context gets a desktop-size window."""
    return {**browser_context_args, "viewport": {"width": 1366, "height": 900}}


@pytest.fixture
def app_page(page: Page, settings: Settings) -> Page:
    """pytest-playwright's page, with ads blocked and the default timeout from the settings."""
    page.set_default_timeout(settings.ui_timeout_ms)
    page.context.route("**/*", _block_ads)
    return page


@pytest.fixture
def login_page(app_page: Page, settings: Settings) -> LoginPage:
    """The login page, opened."""
    return LoginPage(app_page, settings).open()


@pytest.fixture
def notes_page(app_page: Page, settings: Settings, logged_in_client: NotesApiClient) -> NotesPage:
    """The notes home page, already logged in as the test's own user.

    The login goes through the API and the token is put into localStorage before the app loads
    (that is where the app keeps it), so UI tests do not repeat the login form every time.
    """
    app_page.context.add_init_script(f"window.localStorage.setItem('token', '{logged_in_client.token}');")
    return NotesPage(app_page, settings).open()
