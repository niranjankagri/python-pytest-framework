"""Client for the Notes REST API.

One method per endpoint; every method returns the raw requests.Response, so a test can check
status codes and error messages as well as successful bodies (parse those with the models in
framework.api.models). Tests never build URLs or headers themselves.
"""

import requests

from framework.config import Settings
from framework.retry import with_retries

# Header the API reads the session token from
TOKEN_HEADER = "x-auth-token"

# Methods that may be sent again after a timeout: repeating them leaves the server in the same state.
# POST is left out: a repeated create_note would make two notes, a repeated change_password would
# fail because the first one already changed it. A single call can still opt in or out (retry=...).
SAFE_TO_REPEAT = frozenset({"GET", "PUT", "PATCH", "DELETE"})

# The errors of a slow or unreachable server; anything the server actually answers is not retried
NETWORK_ERRORS = (requests.Timeout, requests.ConnectionError)


class NotesApiClient:
    """A requests.Session pointed at the Notes API, optionally logged in."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.api_url
        self._timeout = settings.api_timeout
        self._attempts = settings.attempts
        # One session per client: keeps the connection open between calls
        self._session = requests.Session()
        self.token: str | None = None

    # --- plumbing -------------------------------------------------------------------------------

    def _request(self, method: str, path: str, *, retry: bool | None = None, **kwargs) -> requests.Response:
        """Sends a request; adds the token header when the client is logged in.

        After a timeout or a lost connection the request is sent again (settings.attempts in total)
        if repeating it is harmless: by default for SAFE_TO_REPEAT methods, or as `retry` says.
        """
        headers = kwargs.pop("headers", {})
        if self.token is not None:
            headers.setdefault(TOKEN_HEADER, self.token)

        def send() -> requests.Response:
            return self._session.request(
                method, f"{self._base_url}{path}", headers=headers, timeout=self._timeout, **kwargs
            )

        repeatable = method in SAFE_TO_REPEAT if retry is None else retry
        return with_retries(
            send,
            retry_on=NETWORK_ERRORS,
            attempts=self._attempts if repeatable else 1,
            what=f"{method} {path}",
        )

    def close(self) -> None:
        """Closes the HTTP session."""
        self._session.close()

    # --- health ---------------------------------------------------------------------------------

    def health_check(self) -> requests.Response:
        """GET /health-check: 200 and "Notes API is Running" when the API is up. No token needed."""
        return self._request("GET", "/health-check")

    # --- users ----------------------------------------------------------------------------------

    def register(self, name: str, email: str, password: str) -> requests.Response:
        """POST /users/register: 201 with the new user; 400 for invalid fields, 409 if the email is taken."""
        return self._request(
            "POST", "/users/register", data={"name": name, "email": email, "password": password}
        )

    def login(self, email: str, password: str) -> requests.Response:
        """POST /users/login: 200 with a token, 401 for a wrong email or password.

        On success the client keeps the token and sends it with every later call.
        """
        # A POST, but safe to repeat: logging in again only hands out another token
        response = self._request(
            "POST", "/users/login", data={"email": email, "password": password}, retry=True
        )
        if response.status_code == 200:
            self.token = response.json()["data"]["token"]
        return response

    def get_profile(self) -> requests.Response:
        """GET /users/profile: 200 with the logged-in user; 401 without a valid token."""
        return self._request("GET", "/users/profile")

    def update_profile(self, name: str, phone: str, company: str) -> requests.Response:
        """PATCH /users/profile: 200 with the changed user; 400 if a field is invalid (phone: 8-20 digits)."""
        return self._request(
            "PATCH", "/users/profile", data={"name": name, "phone": phone, "company": company}
        )

    def change_password(self, current_password: str, new_password: str) -> requests.Response:
        """POST /users/change-password: 200 on success; 400 if the current password is wrong."""
        return self._request(
            "POST",
            "/users/change-password",
            data={"currentPassword": current_password, "newPassword": new_password},
        )

    def logout(self) -> requests.Response:
        """DELETE /users/logout: 200, and the token stops working on the server.

        The client keeps the old token on purpose, so a test can prove it is now refused.
        """
        # Not repeated: if the first logout got through, a second one is refused (401) and fails the test
        return self._request("DELETE", "/users/logout", retry=False)

    def delete_account(self) -> requests.Response:
        """DELETE /users/delete-account: removes the logged-in user and all their notes (used by clean-up)."""
        return self._request("DELETE", "/users/delete-account")

    # --- notes ----------------------------------------------------------------------------------

    def create_note(self, title: str, description: str, category: str) -> requests.Response:
        """POST /notes: 200 with the new note (this API answers 200, not 201); 400 if a field is invalid."""
        return self._request(
            "POST", "/notes", data={"title": title, "description": description, "category": category}
        )

    def get_notes(self) -> requests.Response:
        """GET /notes: 200 with all notes of the logged-in user (never another user's)."""
        return self._request("GET", "/notes")

    def get_note(self, note_id: str) -> requests.Response:
        """GET /notes/{id}: 200 with the note; 400 for a malformed id, 404 for an unknown or foreign one."""
        return self._request("GET", f"/notes/{note_id}")

    def update_note(
        self, note_id: str, title: str, description: str, completed: bool, category: str
    ) -> requests.Response:
        """PUT /notes/{id}: replaces every field of the note; 200 with the updated note."""
        return self._request(
            "PUT",
            f"/notes/{note_id}",
            data={
                "title": title,
                "description": description,
                # Form data is text; the API expects "true"/"false"
                "completed": str(completed).lower(),
                "category": category,
            },
        )

    def set_completed(self, note_id: str, completed: bool) -> requests.Response:
        """PATCH /notes/{id}: changes only the completed flag; 200 with the updated note."""
        return self._request("PATCH", f"/notes/{note_id}", data={"completed": str(completed).lower()})

    def delete_note(self, note_id: str) -> requests.Response:
        """DELETE /notes/{id}: 200 when deleted; 404 if it does not exist or belongs to another user."""
        return self._request("DELETE", f"/notes/{note_id}")
