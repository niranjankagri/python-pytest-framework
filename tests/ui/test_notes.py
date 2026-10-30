"""Notes through the web app: add, complete, delete, search and filter."""

import pytest
from playwright.sync_api import expect

from framework.data.factories import new_note

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_tc104_note_added_through_the_form_is_listed(notes_page):
    """A note added through the form appears as a card with its description, and the counter shows 0/1."""
    # Arrange: `notes_page` is already logged in as a new user without notes
    note = new_note("Work")

    # Act: fill and submit the add-note form (waits for the new card)
    notes_page.add_note(note)

    # Assert
    expect(notes_page.card_description(note.title)).to_have_text(note.description)
    expect(notes_page.progress).to_have_text("You have 0/1 notes completed in the all categories")


def test_tc105_completing_a_note_updates_the_progress(notes_page):
    """Completing one of two notes changes the progress line to 1/2."""
    # Arrange: two notes through the form
    first, second = new_note(), new_note()
    notes_page.add_note(first)
    notes_page.add_note(second)

    # Act
    notes_page.toggle_completed(first.title)

    # Assert
    expect(notes_page.progress).to_have_text("You have 1/2 notes completed in the all categories")


def test_tc106_completing_every_note_shows_all_done(notes_page):
    """When every note is completed, the progress line says so."""
    # Arrange
    note = new_note()
    notes_page.add_note(note)

    # Act
    notes_page.toggle_completed(note.title)

    # Assert
    expect(notes_page.progress).to_have_text("You have completed all notes")


def test_tc107_deleted_note_disappears_after_confirming(notes_page):
    """A note deleted through its card and the confirmation dialog is gone from the list."""
    # Arrange
    note = new_note()
    notes_page.add_note(note)

    # Act: delete button, then confirm in the dialog
    notes_page.delete_note(note.title)

    # Assert: no cards left, and the empty-list message
    expect(notes_page.cards).to_have_count(0)
    expect(notes_page.no_notes_message).to_have_text("You don't have any notes in all categories")


def test_tc108_search_shows_only_matching_notes(notes_page):
    """Searching for one note's title shows that note only."""
    # Arrange: two notes with different unique titles
    wanted, other = new_note(), new_note()
    notes_page.add_note(wanted)
    notes_page.add_note(other)

    # Act
    notes_page.search(wanted.title)

    # Assert: the exact list of titles shown, so the other note must be hidden
    expect(notes_page.card_titles).to_have_text([wanted.title])


def test_tc109_search_without_match_says_so(notes_page):
    """A search that matches nothing shows no cards and a 'couldn't find' message."""
    # Arrange: the list is not empty, so the message comes from the search
    notes_page.add_note(new_note())

    # Act
    notes_page.search("no-note-has-this-text")

    # Assert
    expect(notes_page.cards).to_have_count(0)
    expect(notes_page.no_notes_message).to_have_text("Couldn't find any notes in all categories")
