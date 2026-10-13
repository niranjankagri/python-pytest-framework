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
def test_create_note_in_each_category(logged_in_client, category):
    data = new_note(category)

    response = logged_in_client.create_note(data.title, data.description, data.category)

    assert response.status_code == 200
    note = ApiResponse[Note].model_validate(response.json()).data
    assert (note.title, note.description, note.category) == (data.title, data.description, category)
    assert note.completed is False


def test_get_notes_lists_every_note_of_the_user(logged_in_client):
    created = {create(logged_in_client, "Home").id, create(logged_in_client, "Work").id}

    response = logged_in_client.get_notes()

    assert response.status_code == 200
    notes = ApiResponse[list[Note]].model_validate(response.json()).data
    assert {note.id for note in notes} == created


def test_get_note_by_id(logged_in_client):
    note = create(logged_in_client)

    response = logged_in_client.get_note(note.id)

    assert response.status_code == 200
    assert ApiResponse[Note].model_validate(response.json()).data == note


def test_put_replaces_every_field(logged_in_client):
    note = create(logged_in_client, "Home")

    response = logged_in_client.update_note(note.id, "Updated title", "Updated text", True, "Work")

    assert response.status_code == 200
    updated = ApiResponse[Note].model_validate(response.json()).data
    assert (updated.title, updated.description, updated.completed, updated.category) == (
        "Updated title",
        "Updated text",
        True,
        "Work",
    )
    assert updated.updated_at >= note.updated_at


def test_patch_changes_only_the_completed_flag(logged_in_client):
    note = create(logged_in_client)

    response = logged_in_client.set_completed(note.id, True)

    assert response.status_code == 200
    updated = ApiResponse[Note].model_validate(response.json()).data
    assert updated.completed is True
    assert (updated.title, updated.description, updated.category) == (
        note.title,
        note.description,
        note.category,
    )


def test_deleted_note_is_gone(logged_in_client):
    note = create(logged_in_client)

    assert logged_in_client.delete_note(note.id).status_code == 200

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
def test_create_note_validates_its_fields(logged_in_client, title, description, category, message):
    response = logged_in_client.create_note(title, description, category)

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
def test_get_note_with_a_bad_id(logged_in_client, note_id, status, message):
    response = logged_in_client.get_note(note_id)

    assert response.status_code == status
    assert response.json()["message"] == message


def test_users_cannot_see_or_delete_each_others_notes(logged_in_client, settings, second_account):
    note = create(logged_in_client)
    other = NotesApiClient(settings)
    other.login(second_account.email, second_account.password)

    try:
        # 404, not 403: the API does not even confirm that the note exists
        assert other.get_note(note.id).status_code == 404
        assert other.delete_note(note.id).status_code == 404
    finally:
        other.close()
    assert logged_in_client.get_note(note.id).status_code == 200, "the owner's note must be untouched"


def test_notes_require_a_token(api_client):
    response = api_client.get_notes()

    assert response.status_code == 401
