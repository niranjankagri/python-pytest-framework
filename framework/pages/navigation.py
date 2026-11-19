"""Opening a page of the app, shared by all page objects."""

from collections.abc import Callable

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from framework.config import Settings
from framework.retry import with_retries


def open_page(
    page: Page, url: str, settings: Settings, wait_until_ready: Callable[[], None] | None = None
) -> None:
    """Loads url and waits until the page is usable; tries again if the demo is too slow.

    The page load gets its own, longer timeout (settings.ui_navigation_timeout_ms) than clicks and
    fills. wait_until_ready (e.g. "the notes list has loaded") belongs to the same attempt, so a
    page that arrived but never finished loading its data is loaded again too. Reloading is always
    safe: opening a page changes nothing in the app.
    """

    def attempt() -> None:
        page.goto(url, timeout=settings.ui_navigation_timeout_ms)
        if wait_until_ready is not None:
            wait_until_ready()

    with_retries(
        attempt, retry_on=(PlaywrightTimeoutError,), attempts=settings.attempts, what=f"opening {url}"
    )
