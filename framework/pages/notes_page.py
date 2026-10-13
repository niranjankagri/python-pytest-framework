"""The notes home page: list, add-note form, completed switch, delete dialog, search and filters."""

from playwright.sync_api import Locator, Page

from framework.config import Settings
from framework.data.factories import NoteData


class NotesPage:
    """Home page of a logged-in user."""

    def __init__(self, page: Page, settings: Settings) -> None:
        self.page = page
        # The home page of the app is the notes list
        self.url = settings.app_url
        # List and its states
        self.cards = page.get_by_test_id("note-card")
        self.card_titles = page.get_by_test_id("note-card-title")
        self.progress = page.get_by_test_id("progress-info")
        # Shown instead of cards when the list (or a search) is empty
        self.no_notes_message = page.get_by_test_id("no-notes-message")
        # Add-note form (a dialog)
        self.add_button = page.get_by_test_id("add-new-note")
        self.form_category = page.get_by_test_id("note-category")
        self.form_completed = page.get_by_test_id("note-completed")
        self.form_title = page.get_by_test_id("note-title")
        self.form_description = page.get_by_test_id("note-description")
        self.form_submit = page.get_by_test_id("note-submit")
        # Search and category filters
        self.search_input = page.get_by_test_id("search-input")
        self.search_button = page.get_by_test_id("search-btn")
        # Delete confirmation dialog
        self.delete_confirm = page.get_by_test_id("note-delete-confirm")
        self.logout_button = page.get_by_test_id("logout")

    def open(self) -> "NotesPage":
        """Opens the home page and waits until the list has loaded (cards or the empty message)."""
        self.page.goto(self.url)
        self.wait_until_loaded()
        return self

    def wait_until_loaded(self) -> None:
        """Waits until the notes list has finished loading (with or without notes)."""
        # The app shows a spinner first; either the progress line or the empty message ends it.
        # Both are always in the page, one of them hidden (d-none), so wait for the visible one.
        self.progress.or_(self.no_notes_message).filter(visible=True).first.wait_for()

    def card(self, title: str) -> Locator:
        """The card of the note with exactly this title."""
        return self.cards.filter(
            has=self.page.get_by_test_id("note-card-title").get_by_text(title, exact=True)
        )

    def add_note(self, note: NoteData, completed: bool = False) -> None:
        """Creates a note through the form and waits until its card is shown."""
        self.add_button.click()
        self.form_category.select_option(note.category)
        if completed:
            self.form_completed.check()
        self.form_title.fill(note.title)
        self.form_description.fill(note.description)
        self.form_submit.click()
        self.card(note.title).wait_for()

    def toggle_completed(self, title: str) -> None:
        """Flips the completed switch on the note's card."""
        self.card(title).get_by_test_id("toggle-note-switch").click()

    def delete_note(self, title: str) -> None:
        """Deletes the note: delete button, then confirm in the dialog."""
        self.card(title).get_by_test_id("note-delete").click()
        self.delete_confirm.click()
        self.card(title).wait_for(state="detached")

    def search(self, text: str) -> None:
        """Types the text into the search box and submits it; the list then shows only the matching notes."""
        self.search_input.fill(text)
        self.search_button.click()

    def filter_category(self, category: str) -> None:
        """Shows only one category: Home, Work, Personal, or All."""
        self.page.get_by_test_id(f"category-{category.lower()}").click()

    def titles(self) -> list[str]:
        """Titles of the cards shown now."""
        return self.card_titles.all_inner_texts()
