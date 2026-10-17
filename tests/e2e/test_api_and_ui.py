"""Hybrid tests: the API and the web app share one backend, so each side can check the other.

Set-up through the API is fast and reliable; the browser is used only for what the test is about.
"""

import pytest
from playwright.sync_api import expect

from framework.api.models import ApiResponse, Note
from framework.data.factories import new_note

pytestmark = pytest.mark.e2e


def create_via_api(client, category: str = "Home") -> Note:
    """Creates a note through the API (the fast set-up path) and returns it parsed."""
    data = new_note(category)
    response = client.create_note(data.title, data.description, data.category)
    assert response.status_code == 200, response.text
    return ApiResponse[Note].model_validate(response.json()).data


@pytest.mark.smoke
def test_note_created_through_the_api_is_shown_in_the_app(logged_in_client, notes_page):
    """API → UI: a note created through the API is shown in the app with its description."""
    # Arrange: create the note through the API (fast)
    note = create_via_api(logged_in_client, "Personal")

    # Act: reload the app, which reads the notes from the same backend
    notes_page.open()

    # Assert
    expect(notes_page.card_description(note.title)).to_have_text(note.description)


def test_category_filter_shows_only_that_category(logged_in_client, notes_page):
    """API → UI: with one note per category, the Work filter shows only the Work note."""
    # Arrange: one note in each category, through the API
    notes = {
        category: create_via_api(logged_in_client, category) for category in ("Home", "Work", "Personal")
    }
    notes_page.open()

    # Act
    notes_page.filter_category("Work")

    # Assert
    expect(notes_page.card_titles).to_have_text([notes["Work"].title])


def test_note_completed_in_the_app_is_completed_in_the_api(logged_in_client, notes_page):
    """UI → API: a note completed in the app is stored as completed on the server."""
    # Arrange
    note = create_via_api(logged_in_client)
    notes_page.open()

    # Act: complete it in the app, and wait until the app shows the change
    notes_page.toggle_completed(note.title)
    expect(notes_page.progress).to_have_text("You have completed all notes")

    # Assert: read it back through the API
    stored = ApiResponse[Note].model_validate(logged_in_client.get_note(note.id).json()).data
    assert stored.completed is True


def test_note_deleted_in_the_app_is_gone_from_the_api(logged_in_client, notes_page):
    """UI → API: a note deleted in the app no longer exists on the server."""
    # Arrange
    note = create_via_api(logged_in_client)
    notes_page.open()

    # Act
    notes_page.delete_note(note.title)

    # Assert: the API cannot find it any more
    assert logged_in_client.get_note(note.id).status_code == 404


def test_note_changed_through_the_api_shows_the_new_text(logged_in_client, notes_page):
    """API → UI: a note renamed through the API shows the new title after the app reloads."""
    # Arrange: a note that the app already shows
    note = create_via_api(logged_in_client)
    notes_page.open()
    expect(notes_page.card(note.title)).to_be_visible()

    # Act: rename it through the API, then reload the app
    logged_in_client.update_note(note.id, "Renamed through the API", note.description, False, note.category)
    notes_page.open()

    # Assert
    expect(notes_page.card_titles).to_have_text(["Renamed through the API"])
