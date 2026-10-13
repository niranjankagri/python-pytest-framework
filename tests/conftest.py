"""Fixtures shared by all tests: settings, API clients and throwaway user accounts.

Each test that needs a user gets a brand-new account registered through the API, and the
account is deleted afterwards (also when the test failed). So tests never share data, can run
in any order and in parallel, and leave nothing behind on the public demo.
"""

import warnings
from collections.abc import Iterator
from dataclasses import dataclass

import pytest

from framework.api.notes_client import NotesApiClient
from framework.config import Settings, load_settings
from framework.data.factories import new_user


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
