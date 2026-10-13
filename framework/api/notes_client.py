"""Client for the Notes REST API.

One method per endpoint; every method returns the raw requests.Response, so a test can check
status codes and error messages as well as successful bodies (parse those with the models in
framework.api.models). Tests never build URLs or headers themselves.
"""

import requests

from framework.config import Settings

# Header the API reads the session token from
TOKEN_HEADER = "x-auth-token"


class NotesApiClient:
    """A requests.Session pointed at the Notes API, optionally logged in."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.api_url
        self._timeout = settings.api_timeout
        # One session per client: keeps the connection open between calls
        self._session = requests.Session()
        self.token: str | None = None

    # --- plumbing -------------------------------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Sends a request; adds the token header when the client is logged in."""
        headers = kwargs.pop("headers", {})
        if self.token is not None:
            headers.setdefault(TOKEN_HEADER, self.token)
        return self._session.request(
            method, f"{self._base_url}{path}", headers=headers, timeout=self._timeout, **kwargs
        )

    def close(self) -> None:
        """Closes the HTTP session."""
        self._session.close()

    # --- health ---------------------------------------------------------------------------------

    def health_check(self) -> requests.Response:
        return self._request("GET", "/health-check")

    # --- users ----------------------------------------------------------------------------------

    def register(self, name: str, email: str, password: str) -> requests.Response:
        return self._request(
            "POST", "/users/register", data={"name": name, "email": email, "password": password}
        )

    def login(self, email: str, password: str) -> requests.Response:
        """Logs in; on success the client keeps the token and sends it with every later call."""
        response = self._request("POST", "/users/login", data={"email": email, "password": password})
        if response.status_code == 200:
            self.token = response.json()["data"]["token"]
        return response

    def get_profile(self) -> requests.Response:
        return self._request("GET", "/users/profile")

    def update_profile(self, name: str, phone: str, company: str) -> requests.Response:
        return self._request(
            "PATCH", "/users/profile", data={"name": name, "phone": phone, "company": company}
        )

    def change_password(self, current_password: str, new_password: str) -> requests.Response:
        return self._request(
            "POST",
            "/users/change-password",
            data={"currentPassword": current_password, "newPassword": new_password},
        )

    def logout(self) -> requests.Response:
        return self._request("DELETE", "/users/logout")

    def delete_account(self) -> requests.Response:
        return self._request("DELETE", "/users/delete-account")

    # --- notes ----------------------------------------------------------------------------------

    def create_note(self, title: str, description: str, category: str) -> requests.Response:
        return self._request(
            "POST", "/notes", data={"title": title, "description": description, "category": category}
        )

    def get_notes(self) -> requests.Response:
        return self._request("GET", "/notes")

    def get_note(self, note_id: str) -> requests.Response:
        return self._request("GET", f"/notes/{note_id}")

    def update_note(
        self, note_id: str, title: str, description: str, completed: bool, category: str
    ) -> requests.Response:
        """PUT: replaces every field of the note."""
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
        """PATCH: changes only the completed flag."""
        return self._request("PATCH", f"/notes/{note_id}", data={"completed": str(completed).lower()})

    def delete_note(self, note_id: str) -> requests.Response:
        return self._request("DELETE", f"/notes/{note_id}")
