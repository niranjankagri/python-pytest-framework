"""Login through the web form: the one place where UI tests use the real form."""

import re

import pytest
from playwright.sync_api import expect

from framework.pages.notes_page import NotesPage

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_valid_login_opens_the_notes_page(login_page, account, settings):
    login_page.login(account.email, account.password)

    notes = NotesPage(login_page.page, settings)
    expect(login_page.page).to_have_url(re.compile(r"/notes/app/?$"))
    notes.wait_until_loaded()
    expect(notes.no_notes_message).to_have_text("You don't have any notes in all categories")


def test_wrong_password_shows_an_error(login_page, account):
    login_page.login(account.email, "Wrong-Pass-1")

    expect(login_page.alert).to_have_text("Incorrect email address or password")
    expect(login_page.page).to_have_url(login_page.url)


def test_empty_form_asks_for_email_and_password(login_page):
    login_page.submit.click()

    expect(login_page.field_errors).to_have_text(["Email address is required", "Password is required"])
