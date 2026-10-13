"""Report demo: tests that fail, skip and xfail ON PURPOSE, to show each result in the report.

They carry the demo marker, which pytest.ini leaves out of normal runs. Run them with:

    pytest -m demo

Expected: 2 failed, 1 skipped, 1 xfailed. reports/report.html then shows the UI failure with an
embedded screenshot, the API failure with the response message, the skip reason and the xfail
reason; test-results/ holds the trace and video of the UI failure.
"""

import pytest
from playwright.sync_api import expect

from framework.data.factories import new_note

pytestmark = pytest.mark.demo


def test_ui_failure_on_purpose(notes_page):
    notes_page.add_note(new_note())

    # Wrong on purpose: one note was added, the app says 0/1, the test expects 1/1.
    # The report row gets a screenshot of the page at that moment.
    expect(notes_page.progress).to_have_text(
        "You have 1/1 notes completed in the all categories", timeout=3000
    )


def test_api_failure_on_purpose(api_client, account):
    response = api_client.login(account.email, "Wrong-Pass-1")

    # Wrong on purpose: a wrong password gets 401; the message shows what the API said
    assert response.status_code == 200, f"demo failure, API answered: {response.json()['message']}"


def test_skipped_on_purpose():
    pytest.skip("Skipped on purpose to show a skipped test and its reason in the report")


@pytest.mark.xfail(reason="Demo of a known bug: xfail records it without failing the run", strict=True)
def test_known_bug_xfail_on_purpose(api_client):
    # strict=True: if this ever passes, pytest reports XPASS(strict) as a failure,
    # a reminder to remove the xfail once the bug is fixed
    assert api_client.health_check().json()["message"] == "Notes API is Down"
