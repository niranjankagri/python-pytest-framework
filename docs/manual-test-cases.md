# Manual test cases

The test cases this framework automates, written as a tester would run them by hand. Every case has
an ID; the pytest function that covers it starts with the same ID (`test_tc214_create_note_in_each_category`),
so a failure in the report leads straight to the case below, and one case runs with
`pytest -k tc214`. Parametrized tests are one case with several data sets (`[Home]`, `[Work]` ...).

| ID range | Area | Automated in |
|---|---|---|
| TC-101 to TC-109 | Notes web app: login and notes | `tests/ui/` (Playwright) |
| TC-110 to TC-114 | API and web app together (hybrid) | `tests/e2e/` |
| TC-201 to TC-223 | Notes REST API | `tests/api/` (requests + pydantic) |

Not listed: `tests/demo/` (fails, skips and xfails on purpose to show the report).

## Setup

- Web app: <https://practice.expandtesting.com/notes/app>; API:
  <https://practice.expandtesting.com/notes/api> (public, shared).
- A fresh account per case: register one in the app or with `POST /users/register`, e.g. name
  `Pytest User a1b2c3`, e-mail `pytest.a1b2c3d4e5@example.com`, password `Pw-a1b2c3d4e5`.
- API calls send form fields; protected calls need header `x-auth-token: <token from login>`.
- Categories: Home, Work, Personal.

## Summary

| ID | Title | Type | Priority |
|---|---|---|---|
| TC-101 | Valid login opens the (empty) notes page | UI / Smoke | High |
| TC-102 | Wrong password shows an error | UI / Negative | High |
| TC-103 | Empty login form asks for e-mail and password | UI / Negative | Medium |
| TC-104 | A note added through the form is listed | UI / Smoke | High |
| TC-105 | Completing one of two notes updates the progress | UI | Medium |
| TC-106 | Completing every note shows "all done" | UI | Low |
| TC-107 | A deleted note disappears after confirming | UI | High |
| TC-108 | Search shows only the matching note | UI | Medium |
| TC-109 | Search without a match says so | UI / Negative | Low |
| TC-110 | A note created through the API is shown in the app | Hybrid / Smoke | High |
| TC-111 | The category filter shows only that category | Hybrid | Medium |
| TC-112 | A note completed in the app is completed in the API | Hybrid | High |
| TC-113 | A note deleted in the app is gone from the API | Hybrid | High |
| TC-114 | A note changed through the API shows the new text | Hybrid | Medium |
| TC-201 | The API reports it is running | API / Smoke | High |
| TC-202 | Register returns the new user | API / Smoke | High |
| TC-203 | Register refuses an e-mail that is taken | API / Negative | High |
| TC-204 | Register validates its fields (3 data sets) | API / Negative | Medium |
| TC-205 | Login returns a token | API / Smoke | High |
| TC-206 | Login failure does not reveal which part was wrong (2 data sets) | API / Security | High |
| TC-207 | Profile returns the logged-in user | API | Medium |
| TC-208 | Profile requires a valid token (2 data sets) | API / Security | High |
| TC-209 | Profile update returns the new values | API | Medium |
| TC-210 | Profile update validates the phone number | API / Negative | Low |
| TC-211 | A changed password replaces the old one | API / Security | High |
| TC-212 | Changing the password checks the current one | API / Security | High |
| TC-213 | Logout invalidates the token | API / Security | High |
| TC-214 | Create a note in each category (3 data sets) | API / Smoke | High |
| TC-215 | The list contains exactly the user's notes | API | High |
| TC-216 | Get a note by id | API | Medium |
| TC-217 | PUT replaces every field | API | Medium |
| TC-218 | PATCH changes only the completed flag | API | Medium |
| TC-219 | A deleted note is gone | API | High |
| TC-220 | Create note validates its fields (3 data sets) | API / Negative | Medium |
| TC-221 | Get a note with a bad id (2 data sets) | API / Negative | Low |
| TC-222 | Users cannot see or delete each other's notes | API / Security | High |
| TC-223 | Notes require a token | API / Security | High |

---

## UI: login (`tests/ui/test_login.py`)

Precondition for all: a registered account; the app's login page is open.

### TC-101 Valid login opens the (empty) notes page

| # | Step | Expected result |
|---|---|---|
| 1 | Enter the account's e-mail and password, click **Login** | The notes page: "You don't have any notes in all categories" |

### TC-102 Wrong password shows an error

| # | Step | Expected result |
|---|---|---|
| 1 | Enter the e-mail and a wrong password, click **Login** | "Incorrect email address or password"; still on the login page |

### TC-103 Empty login form asks for e-mail and password

| # | Step | Expected result |
|---|---|---|
| 1 | Click **Login** without entering anything | "Email address is required" and "Password is required" under the fields |

## UI: notes (`tests/ui/test_notes.py`)

Precondition for all: logged in with a fresh account (no notes).

### TC-104 A note added through the form is listed

| # | Step | Expected result |
|---|---|---|
| 1 | **+ Add Note**: category Home, title `Note a1b2c3d4e5`, description `Created by pytest (a1b2c3d4e5)`, **Create** | A card with the title and description |
| 2 | Read the progress line | "You have 0/1 notes completed in the all categories" |

### TC-105 Completing one of two notes updates the progress

| # | Step | Expected result |
|---|---|---|
| 1 | Add two notes; switch one card's toggle to completed | "You have 1/2 notes completed in the all categories" |

### TC-106 Completing every note shows "all done"

| # | Step | Expected result |
|---|---|---|
| 1 | Add notes and complete all of them | "You have completed all notes" |

### TC-107 A deleted note disappears after confirming

| # | Step | Expected result |
|---|---|---|
| 1 | Add a note; **Delete** on its card; **Delete** in the confirmation dialog | The card is gone; "You don't have any notes in all categories" |

### TC-108 Search shows only the matching note

| # | Step | Expected result |
|---|---|---|
| 1 | Add two notes; search for the first one's title | Only that note's card |

### TC-109 Search without a match says so

| # | Step | Expected result |
|---|---|---|
| 1 | Search for a title that does not exist | No cards; "Couldn't find any notes in all categories" |

## Hybrid: API and app (`tests/e2e/test_api_and_ui.py`)

Precondition for all: an account, logged in both in the app and through the API (token).

### TC-110 A note created through the API is shown in the app

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /notes` with a title, description and category | `200` |
| 2 | Reload the app | A card with that title and description |

### TC-111 The category filter shows only that category

| # | Step | Expected result |
|---|---|---|
| 1 | Create one note per category through the API; reload the app; click the **Work** filter | Only the Work note |

### TC-112 A note completed in the app is completed in the API

| # | Step | Expected result |
|---|---|---|
| 1 | Create a note through the API; in the app switch it to completed | "You have completed all notes" |
| 2 | `GET /notes/<id>` | `completed: true` |

### TC-113 A note deleted in the app is gone from the API

| # | Step | Expected result |
|---|---|---|
| 1 | Create a note through the API; delete it in the app (confirm) | Card gone |
| 2 | `GET /notes/<id>` | `404` |

### TC-114 A note changed through the API shows the new text

| # | Step | Expected result |
|---|---|---|
| 1 | Create a note; `PUT /notes/<id>` with title `Renamed through the API`; reload the app | The card shows "Renamed through the API" |

---

## API: health and users (`tests/api/test_health.py`, `test_users.py`)

### TC-201 The API reports it is running

| # | Step | Expected result |
|---|---|---|
| 1 | `GET /health-check` | `200`; `success: true`, message "Notes API is Running" |

### TC-202 Register returns the new user

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /users/register` with a new name, e-mail and password | `201`; "User account created successfully"; the user's name and e-mail in `data` |

### TC-203 Register refuses an e-mail that is taken

| # | Step | Expected result |
|---|---|---|
| 1 | Register again with an existing e-mail | `409`; "An account already exists with the same email address" |

### TC-204 Register validates its fields

Each data set: register with one invalid field (the others valid). Expected `400` and the message.

| Data set | Field | Value | Message |
|---|---|---|---|
| invalid-email | email | `not-an-email` | A valid email address is required |
| name-too-short | name | `Abc` | User name must be between 4 and 30 characters |
| password-too-short | password | `12345` | Password must be between 6 and 30 characters |

### TC-205 Login returns a token

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /users/login` with e-mail and password | `200`; the user's e-mail and a `token` of 64 hex characters |

### TC-206 Login failure does not reveal which part was wrong

| Data set | Login with | Expected result |
|---|---|---|
| wrong-password | the account's e-mail, a wrong password | `401`, "Incorrect email address or password" |
| unknown-user | an unregistered e-mail | Exactly the same answer |

### TC-207 Profile returns the logged-in user

| # | Step | Expected result |
|---|---|---|
| 1 | `GET /users/profile` with the token | `200`; the account's name and e-mail |

### TC-208 Profile requires a valid token

| Data set | Header | Expected result |
|---|---|---|
| no-token | none | `401`, "No authentication token specified in x-auth-token header" |
| invalid-token | `x-auth-token: not-a-real-token` | `401`, "Access token is not valid or has expired, you will need to login" |

### TC-209 Profile update returns the new values

| # | Step | Expected result |
|---|---|---|
| 1 | `PATCH /users/profile` name `Updated Name`, phone `01234567890`, company `Acme QA` | `200`; the new values returned and stored |

### TC-210 Profile update validates the phone number

| # | Step | Expected result |
|---|---|---|
| 1 | `PATCH /users/profile` with a phone of fewer than 8 digits | `400`; "Phone number should be between 8 and 20 digits" |

### TC-211 A changed password replaces the old one

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /users/change-password` with the current and a new password | `200` |
| 2 | Log in with the old password; then with the new one | Old: `401`; new: `200` |

### TC-212 Changing the password checks the current one

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /users/change-password` with a wrong current password | `400`; "The current password is incorrect" |

### TC-213 Logout invalidates the token

| # | Step | Expected result |
|---|---|---|
| 1 | `DELETE /users/logout` with the token | `200` |
| 2 | `GET /users/profile` with the same token | `401` |

## API: notes (`tests/api/test_notes.py`)

Precondition for all: logged in through the API (token).

### TC-214 Create a note in each category

Data sets: `Home`, `Work`, `Personal`.

| # | Step | Expected result |
|---|---|---|
| 1 | `POST /notes` with title, description and the category | `200`; title, description and category as sent; `completed: false` |

### TC-215 The list contains exactly the user's notes

| # | Step | Expected result |
|---|---|---|
| 1 | Create some notes; `GET /notes` | `200`; exactly the ids just created, no others |

### TC-216 Get a note by id

| # | Step | Expected result |
|---|---|---|
| 1 | Create a note; `GET /notes/<id>` | `200`; the same note as the create answer |

### TC-217 PUT replaces every field

| # | Step | Expected result |
|---|---|---|
| 1 | Create a note; `PUT /notes/<id>` with a new title, description, category and `completed: true` | `200`; all four fields changed; `updated_at` not earlier than before |

### TC-218 PATCH changes only the completed flag

| # | Step | Expected result |
|---|---|---|
| 1 | Create a note; `PATCH /notes/<id>` `completed=true` | `200`; `completed: true`; title, description and category unchanged |

### TC-219 A deleted note is gone

| # | Step | Expected result |
|---|---|---|
| 1 | Create a note; `DELETE /notes/<id>` | `200` |
| 2 | `GET /notes/<id>` | `404`; "No note was found with the provided ID, Maybe it was deleted" |

### TC-220 Create note validates its fields

Each data set: `POST /notes`; expected `400` and the message.

| Data set | Title | Description | Category | Message |
|---|---|---|---|---|
| title-too-short | `Abc` | `Long enough` | Home | Title must be between 4 and 100 characters |
| description-too-short | `Valid title` | `Abc` | Home | Description must be between 4 and 1000 characters |
| unknown-category | `Valid title` | `Long enough` | Hobby | Category must be one of the categories: Home, Work, Personal |

### TC-221 Get a note with a bad id

| Data set | Request | Expected result |
|---|---|---|
| malformed-id | `GET /notes/123` | `400`, "Note ID must be a valid ID" |
| unknown-id | `GET /notes/6ace0ca52d855102960a16ec` | `404`, "No note was found with the provided ID, Maybe it was deleted" |

### TC-222 Users cannot see or delete each other's notes

| # | Step | Expected result |
|---|---|---|
| 1 | User A creates a note; user B (second account) `GET`s and `DELETE`s it with B's token | `404` both times (no IDOR / BOLA hole) |
| 2 | User A reads the note | `200`, untouched |

### TC-223 Notes require a token

| # | Step | Expected result |
|---|---|---|
| 1 | `GET /notes` without `x-auth-token` | `401` |
