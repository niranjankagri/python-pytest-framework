"""User endpoints: register, login, profile, password and logout, with their error cases."""

import re

import pytest

from framework.api.models import ApiResponse, LoginData, User
from framework.data.factories import new_user

pytestmark = pytest.mark.api


# --- register ---------------------------------------------------------------------------------


@pytest.mark.smoke
def test_register_returns_the_new_user(api_client, unregistered_cleanup):
    user = new_user()

    response = api_client.register(user.name, user.email, user.password)
    unregistered_cleanup.append((user.email, user.password))

    assert response.status_code == 201
    body = ApiResponse[User].model_validate(response.json())
    assert body.message == "User account created successfully"
    assert (body.data.name, body.data.email) == (user.name, user.email)


def test_register_refuses_an_email_that_is_taken(api_client, account):
    response = api_client.register("Someone Else", account.email, "Other-Pass-1")

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
def test_register_validates_its_fields(api_client, unregistered_cleanup, field, value, message):
    user = new_user()
    data = {"name": user.name, "email": user.email, "password": user.password, field: value}

    response = api_client.register(data["name"], data["email"], data["password"])
    if response.status_code == 201:  # only if the API wrongly accepted it: still clean up
        unregistered_cleanup.append((data["email"], data["password"]))

    assert response.status_code == 400
    assert response.json()["message"] == message


# --- login ------------------------------------------------------------------------------------


@pytest.mark.smoke
def test_login_returns_a_token(api_client, account):
    response = api_client.login(account.email, account.password)

    assert response.status_code == 200
    data = ApiResponse[LoginData].model_validate(response.json()).data
    assert data.email == account.email
    assert re.fullmatch(r"[0-9a-f]{64}", data.token), "token should be 64 hex characters"


@pytest.mark.parametrize("case", ["wrong-password", "unknown-user"])
def test_login_failure_does_not_reveal_which_part_was_wrong(api_client, account, case):
    email = account.email if case == "wrong-password" else new_user().email

    response = api_client.login(email, "Wrong-Pass-1")

    # Same answer for both cases, so the API does not tell attackers which emails exist
    assert response.status_code == 401
    assert response.json()["message"] == "Incorrect email address or password"


# --- profile ----------------------------------------------------------------------------------


def test_profile_returns_the_logged_in_user(logged_in_client, account):
    response = logged_in_client.get_profile()

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
def test_profile_requires_a_valid_token(api_client, token, message):
    api_client.token = token

    response = api_client.get_profile()

    assert response.status_code == 401
    assert response.json()["message"] == message


def test_profile_update_returns_the_new_values(logged_in_client):
    response = logged_in_client.update_profile(name="Updated Name", phone="01234567890", company="Acme QA")

    assert response.status_code == 200
    user = ApiResponse[User].model_validate(response.json()).data
    assert (user.name, user.phone, user.company) == ("Updated Name", "01234567890", "Acme QA")


def test_profile_update_validates_the_phone_number(logged_in_client):
    response = logged_in_client.update_profile(name="Updated Name", phone="123", company="Acme QA")

    assert response.status_code == 400
    assert response.json()["message"] == "Phone number should be between 8 and 20 digits"


# --- password and logout ----------------------------------------------------------------------


def test_changed_password_replaces_the_old_one(logged_in_client, api_client, account):
    new_password = "Changed-Pass-1"

    response = logged_in_client.change_password(account.password, new_password)
    old_password, account.password = account.password, new_password  # clean-up needs the new one

    assert response.status_code == 200
    assert api_client.login(account.email, old_password).status_code == 401
    assert api_client.login(account.email, new_password).status_code == 200


def test_change_password_checks_the_current_password(logged_in_client):
    response = logged_in_client.change_password("Not-The-Password-1", "Changed-Pass-1")

    assert response.status_code == 400
    assert response.json()["message"] == "The current password is incorrect"


def test_logout_invalidates_the_token(logged_in_client):
    assert logged_in_client.logout().status_code == 200

    response = logged_in_client.get_profile()

    assert response.status_code == 401
