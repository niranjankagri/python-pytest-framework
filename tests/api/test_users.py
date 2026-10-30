"""User endpoints: register, login, profile, password and logout, with their error cases."""

import re

import pytest

from framework.api.models import ApiResponse, LoginData, User
from framework.data.factories import new_user

pytestmark = pytest.mark.api


# --- register ---------------------------------------------------------------------------------


@pytest.mark.smoke
def test_tc202_register_returns_the_new_user(api_client, unregistered_cleanup):
    """A new user can register: 201, a confirmation message and the user's own name and email back."""
    # Arrange: unique name, email and password for this test
    user = new_user()

    # Act
    response = api_client.register(user.name, user.email, user.password)
    # This test registers the user itself, so it tells the clean-up fixture to delete it
    unregistered_cleanup.append((user.email, user.password))

    # Assert: status, message and the returned user (contract checked by User)
    assert response.status_code == 201
    body = ApiResponse[User].model_validate(response.json())
    assert body.message == "User account created successfully"
    assert (body.data.name, body.data.email) == (user.name, user.email)


def test_tc203_register_refuses_an_email_that_is_taken(api_client, account):
    """Registering with an email that already has an account fails with 409 Conflict."""
    # Act: the `account` fixture has already registered this email
    response = api_client.register("Someone Else", account.email, "Other-Pass-1")

    # Assert
    assert response.status_code == 409
    assert response.json()["message"] == "An account already exists with the same email address"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("email", "not-an-email", "A valid email address is required"),
        ("name", "Abc", "User name must be between 4 and 30 characters"),
        ("password", "12345", "Password must be between 6 and 30 characters"),
    ],
    ids=["invalid-email", "name-too-short", "password-too-short"],
)
def test_tc204_register_validates_its_fields(api_client, unregistered_cleanup, field, value, message):
    """Each invalid field is refused with 400 and its own message (one report row per case)."""
    # Arrange: a valid user, with one field replaced by the invalid value of this case
    user = new_user()
    data = {"name": user.name, "email": user.email, "password": user.password, field: value}

    # Act
    response = api_client.register(data["name"], data["email"], data["password"])
    if response.status_code == 201:  # only if the API wrongly accepted it: still clean up
        unregistered_cleanup.append((data["email"], data["password"]))

    # Assert: refused, with the message for this field
    assert response.status_code == 400
    assert response.json()["message"] == message


# --- login ------------------------------------------------------------------------------------


@pytest.mark.smoke
def test_tc205_login_returns_a_token(api_client, account):
    """Logging in with the right password returns the user's email and a 64-character hex token."""
    # Act
    response = api_client.login(account.email, account.password)

    # Assert: the body matches LoginData, and the token has the expected format
    assert response.status_code == 200
    data = ApiResponse[LoginData].model_validate(response.json()).data
    assert data.email == account.email
    assert re.fullmatch(r"[0-9a-f]{64}", data.token), "token should be 64 hex characters"


@pytest.mark.parametrize("case", ["wrong-password", "unknown-user"])
def test_tc206_login_failure_does_not_reveal_which_part_was_wrong(api_client, account, case):
    """A wrong password and an unknown email get exactly the same 401 answer.

    Different answers would let an attacker find out which emails have an account.
    """
    # Arrange: a registered email (wrong-password case) or one that was never registered
    email = account.email if case == "wrong-password" else new_user().email

    # Act
    response = api_client.login(email, "Wrong-Pass-1")

    # Same answer for both cases, so the API does not tell attackers which emails exist
    assert response.status_code == 401
    assert response.json()["message"] == "Incorrect email address or password"


# --- profile ----------------------------------------------------------------------------------


def test_tc207_profile_returns_the_logged_in_user(logged_in_client, account):
    """The profile endpoint returns the user that the token belongs to."""
    # Act: the client sends the token of `account`
    response = logged_in_client.get_profile()

    # Assert: the same name and email as registered
    assert response.status_code == 200
    user = ApiResponse[User].model_validate(response.json()).data
    assert (user.name, user.email) == (account.name, account.email)


@pytest.mark.parametrize(
    ("token", "message"),
    [
        (None, "No authentication token specified in x-auth-token header"),
        ("not-a-real-token", "Access token is not valid or has expired, you will need to login"),
    ],
    ids=["no-token", "invalid-token"],
)
def test_tc208_profile_requires_a_valid_token(api_client, token, message):
    """Without a token, or with an invalid one, the profile is refused with 401 and a clear message."""
    # Arrange: no token at all, or one the server never issued
    api_client.token = token

    # Act
    response = api_client.get_profile()

    # Assert
    assert response.status_code == 401
    assert response.json()["message"] == message


def test_tc209_profile_update_returns_the_new_values(logged_in_client):
    """Updating the profile stores the new name, phone and company and returns them."""
    # Act
    response = logged_in_client.update_profile(name="Updated Name", phone="01234567890", company="Acme QA")

    # Assert: the response already shows the new values
    assert response.status_code == 200
    user = ApiResponse[User].model_validate(response.json()).data
    assert (user.name, user.phone, user.company) == ("Updated Name", "01234567890", "Acme QA")


def test_tc210_profile_update_validates_the_phone_number(logged_in_client):
    """A phone number shorter than 8 digits is refused with 400 and the rule in the message."""
    # Act: 3 digits, the API needs 8-20
    response = logged_in_client.update_profile(name="Updated Name", phone="123", company="Acme QA")

    # Assert
    assert response.status_code == 400
    assert response.json()["message"] == "Phone number should be between 8 and 20 digits"


# --- password and logout ----------------------------------------------------------------------


def test_tc211_changed_password_replaces_the_old_one(logged_in_client, api_client, account):
    """After a password change, only the new password works for logging in."""
    # Arrange
    new_password = "Changed-Pass-1"

    # Act
    response = logged_in_client.change_password(account.password, new_password)
    old_password, account.password = account.password, new_password  # clean-up needs the new one

    # Assert: changed, the old password is refused, the new one works
    assert response.status_code == 200
    assert api_client.login(account.email, old_password).status_code == 401
    assert api_client.login(account.email, new_password).status_code == 200


def test_tc212_change_password_checks_the_current_password(logged_in_client):
    """The password cannot be changed without the correct current password (400)."""
    # Act: a wrong current password
    response = logged_in_client.change_password("Not-The-Password-1", "Changed-Pass-1")

    # Assert
    assert response.status_code == 400
    assert response.json()["message"] == "The current password is incorrect"


def test_tc213_logout_invalidates_the_token(logged_in_client):
    """After logout the same token is refused, so a stolen token stops working once the user logs out."""
    # Arrange: log out (the client keeps the old token)
    assert logged_in_client.logout().status_code == 200

    # Act: use the old token again
    response = logged_in_client.get_profile()

    # Assert: the server no longer accepts it
    assert response.status_code == 401
