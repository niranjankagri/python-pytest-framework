"""Settings for a test run, read from environment variables with sensible defaults.

Nothing environment-specific is hard-coded in tests or page objects: point a run at another
environment with e.g. NOTES_APP_URL=... NOTES_API_URL=... pytest
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Where the app and its API live, and how long to wait for them."""

    app_url: str
    api_url: str
    # Seconds for one HTTP call (connect + read) to the API
    api_timeout: float
    # Milliseconds Playwright waits for an element (click, fill, wait_for)
    ui_timeout_ms: int
    # Milliseconds one page load may take; longer than ui_timeout_ms, the demo is sometimes slow
    ui_navigation_timeout_ms: int
    # Milliseconds to wait for what the app shows after a server round trip: a saved or deleted
    # note, the loaded list, a search result, the progress text (also expect()'s default)
    ui_server_timeout_ms: int
    # How often a timed-out page load or API call is tried in total (framework/retry.py); 1 = no retry
    attempts: int


def load_settings() -> Settings:
    """Build the settings from the environment; every value has a default for the public demo."""
    return Settings(
        app_url=os.getenv("NOTES_APP_URL", "https://practice.expandtesting.com/notes/app").rstrip("/"),
        api_url=os.getenv("NOTES_API_URL", "https://practice.expandtesting.com/notes/api").rstrip("/"),
        api_timeout=float(os.getenv("NOTES_API_TIMEOUT", "30")),
        ui_timeout_ms=int(os.getenv("NOTES_UI_TIMEOUT_MS", "15000")),
        ui_navigation_timeout_ms=int(os.getenv("NOTES_UI_NAVIGATION_TIMEOUT_MS", "30000")),
        ui_server_timeout_ms=int(os.getenv("NOTES_UI_SERVER_TIMEOUT_MS", "30000")),
        attempts=max(1, int(os.getenv("NOTES_ATTEMPTS", "3"))),
    )
