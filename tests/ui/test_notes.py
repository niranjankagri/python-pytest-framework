"""Notes through the web app: add, complete, delete, search and filter."""

import pytest
from playwright.sync_api import expect

from framework.data.factories import new_note

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_note_added_through_the_form_is_listed(notes_page):
    note = new_note("Work")

    notes_page.add_note(note)

    card = notes_page.card(note.title)
    expect(card.get_by_test_id("note-card-description")).to_have_text(note.description)
    expect(notes_page.progress).to_have_text("You have 0/1 notes completed in the all categories")


def test_completing_a_note_updates_the_progress(notes_page):
    first, second = new_note(), new_note()
    notes_page.add_note(first)
    notes_page.add_note(second)

    notes_page.toggle_completed(first.title)

    expect(notes_page.progress).to_have_text("You have 1/2 notes completed in the all categories")


def test_completing_every_note_shows_all_done(notes_page):
    note = new_note()
    notes_page.add_note(note)

    notes_page.toggle_completed(note.title)

    expect(notes_page.progress).to_have_text("You have completed all notes")


def test_deleted_note_disappears_after_confirming(notes_page):
    note = new_note()
    notes_page.add_note(note)

    notes_page.delete_note(note.title)

    expect(notes_page.cards).to_have_count(0)
    expect(notes_page.no_notes_message).to_have_text("You don't have any notes in all categories")


def test_search_shows_only_matching_notes(notes_page):
    wanted, other = new_note(), new_note()
    notes_page.add_note(wanted)
    notes_page.add_note(other)

    notes_page.search(wanted.title)

    expect(notes_page.card_titles).to_have_text([wanted.title])


def test_search_without_match_says_so(notes_page):
    notes_page.add_note(new_note())

    notes_page.search("no-note-has-this-text")

    expect(notes_page.cards).to_have_count(0)
    expect(notes_page.no_notes_message).to_have_text("Couldn't find any notes in all categories")
