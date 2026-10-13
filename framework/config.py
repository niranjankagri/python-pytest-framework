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
    # Milliseconds Playwright waits for an element or a navigation
    ui_timeout_ms: int


def load_settings() -> Settings:
    """Build the settings from the environment; every value has a default for the public demo."""
    return Settings(
        app_url=os.getenv("NOTES_APP_URL", "https://practice.expandtesting.com/notes/app").rstrip("/"),
        api_url=os.getenv("NOTES_API_URL", "https://practice.expandtesting.com/notes/api").rstrip("/"),
        api_timeout=float(os.getenv("NOTES_API_TIMEOUT", "30")),
        ui_timeout_ms=int(os.getenv("NOTES_UI_TIMEOUT_MS", "15000")),
    )
