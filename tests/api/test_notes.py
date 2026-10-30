"""Note endpoints: create, read, update, complete and delete, with validation and access rules."""

import pytest

from framework.api.models import ApiResponse, Note
from framework.api.notes_client import NotesApiClient
from framework.data.factories import new_note

pytestmark = pytest.mark.api


def create(client, category: str = "Home") -> Note:
    """Creates a note through the API and returns it parsed."""
    data = new_note(category)
    response = client.create_note(data.title, data.description, data.category)
    assert response.status_code == 200, response.text
    return ApiResponse[Note].model_validate(response.json()).data


@pytest.mark.smoke
@pytest.mark.parametrize("category", ["Home", "Work", "Personal"])
def test_tc214_create_note_in_each_category(logged_in_client, category):
    """A note can be created in each of the three categories, and the API returns exactly what was sent."""
    # Arrange: unique title and description, category of this case
    data = new_note(category)

    # Act
    response = logged_in_client.create_note(data.title, data.description, data.category)

    # Assert: this API answers 200 (not 201); a new note is not completed
    assert response.status_code == 200
    note = ApiResponse[Note].model_validate(response.json()).data
    assert (note.title, note.description, note.category) == (data.title, data.description, category)
    assert note.completed is False


def test_tc215_get_notes_lists_every_note_of_the_user(logged_in_client):
    """The list contains exactly the user's own notes: no more, no fewer."""
    # Arrange: two notes through the API (the user is new, so these are all of them)
    created = {create(logged_in_client, "Home").id, create(logged_in_client, "Work").id}

    # Act
    response = logged_in_client.get_notes()

    # Assert: compare sets of ids, the order does not matter
    assert response.status_code == 200
    notes = ApiResponse[list[Note]].model_validate(response.json()).data
    assert {note.id for note in notes} == created


def test_tc216_get_note_by_id(logged_in_client):
    """Reading a note by id returns the same note that creating it returned."""
    # Arrange
    note = create(logged_in_client)

    # Act
    response = logged_in_client.get_note(note.id)

    # Assert: pydantic models compare field by field
    assert response.status_code == 200
    assert ApiResponse[Note].model_validate(response.json()).data == note


def test_tc217_put_replaces_every_field(logged_in_client):
    """PUT replaces all fields of a note and moves its updated_at forward."""
    # Arrange
    note = create(logged_in_client, "Home")

    # Act: change every field
    response = logged_in_client.update_note(note.id, "Updated title", "Updated text", True, "Work")

    # Assert: every field has its new value
    assert response.status_code == 200
    updated = ApiResponse[Note].model_validate(response.json()).data
    assert (updated.title, updated.description, updated.completed, updated.category) == (
        "Updated title",
        "Updated text",
        True,
        "Work",
    )
    assert updated.updated_at >= note.updated_at


def test_tc218_patch_changes_only_the_completed_flag(logged_in_client):
    """PATCH changes the completed flag and leaves every other field as it was."""
    # Arrange
    note = create(logged_in_client)

    # Act
    response = logged_in_client.set_completed(note.id, True)

    # Assert: completed changed, title, description and category did not
    assert response.status_code == 200
    updated = ApiResponse[Note].model_validate(response.json()).data
    assert updated.completed is True
    assert (updated.title, updated.description, updated.category) == (
        note.title,
        note.description,
        note.category,
    )


def test_tc219_deleted_note_is_gone(logged_in_client):
    """A deleted note can no longer be read: 404 with the not-found message."""
    # Arrange
    note = create(logged_in_client)

    # Act
    assert logged_in_client.delete_note(note.id).status_code == 200

    # Assert: reading it again finds nothing
    response = logged_in_client.get_note(note.id)
    assert response.status_code == 404
    assert response.json()["message"] == "No note was found with the provided ID, Maybe it was deleted"


@pytest.mark.parametrize(
    ("title", "description", "category", "message"),
    [
        ("Abc", "Long enough", "Home", "Title must be between 4 and 100 characters"),
        ("Valid title", "Abc", "Home", "Description must be between 4 and 1000 characters"),
        (
            "Valid title",
            "Long enough",
            "Hobby",
            "Category must be one of the categories: Home, Work, Personal",
        ),
    ],
    ids=["title-too-short", "description-too-short", "unknown-category"],
)
def test_tc220_create_note_validates_its_fields(logged_in_client, title, description, category, message):
    """Each invalid field of a new note is refused with 400 and its own message."""
    # Act: one invalid value per case, the other fields valid
    response = logged_in_client.create_note(title, description, category)

    # Assert
    assert response.status_code == 400
    assert response.json()["message"] == message


@pytest.mark.parametrize(
    ("note_id", "status", "message"),
    [
        ("123", 400, "Note ID must be a valid ID"),
        ("6ace0ca52d855102960a16ec", 404, "No note was found with the provided ID, Maybe it was deleted"),
    ],
    ids=["malformed-id", "unknown-id"],
)
def test_tc221_get_note_with_a_bad_id(logged_in_client, note_id, status, message):
    """A malformed id is a client error (400); a well-formed id that does not exist is 404."""
    # Act
    response = logged_in_client.get_note(note_id)

    # Assert
    assert response.status_code == status
    assert response.json()["message"] == message


def test_tc222_users_cannot_see_or_delete_each_others_notes(logged_in_client, settings, second_account):
    """Another logged-in user can neither read nor delete a user's note (no IDOR / BOLA hole)."""
    # Arrange: user A owns a note; user B logs in with its own client
    note = create(logged_in_client)
    other = NotesApiClient(settings)
    other.login(second_account.email, second_account.password)

    try:
        # 404, not 403: the API does not even confirm that the note exists
        assert other.get_note(note.id).status_code == 404
        assert other.delete_note(note.id).status_code == 404
    finally:
        other.close()
    # And the failed delete really did nothing: the owner can still read the note
    assert logged_in_client.get_note(note.id).status_code == 200, "the owner's note must be untouched"


def test_tc223_notes_require_a_token(api_client):
    """The notes cannot be listed without logging in."""
    # Act: a client that never logged in
    response = api_client.get_notes()

    # Assert
    assert response.status_code == 401
