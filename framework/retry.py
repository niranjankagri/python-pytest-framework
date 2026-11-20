"""Retry for slow answers from the public demo site.

practice.expandtesting.com is a free shared demo and sometimes takes longer than the timeout to
answer a page load or an API call. Without a retry, one slow moment fails a whole batch of tests
that have nothing wrong with them.

Only timeouts and lost connections are retried, never a wrong answer: a 400, a wrong body or a
missing element still fails the test at once. And a call is only retried when sending it twice is
harmless (see NotesApiClient for which API calls qualify).
"""

import logging
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

log = logging.getLogger(__name__)


def with_retries(
    action: Callable[[], T],
    *,
    retry_on: tuple[type[BaseException], ...],
    attempts: int,
    what: str,
    backoff_seconds: float = 2.0,
) -> T:
    """Runs action() up to `attempts` times while it raises one of `retry_on`; returns its result.

    Waits backoff_seconds, then twice that, and so on between attempts, so a busy server gets a
    moment to recover. The last error is raised unchanged, so a real outage still shows its cause.
    Every retry is logged; pytest shows these lines in the report of a test that still failed.
    """
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except retry_on as error:
            if attempt == attempts:
                raise
            wait = backoff_seconds * attempt
            log.warning(
                "%s: attempt %d of %d failed (%s), retrying in %.0f s",
                what,
                attempt,
                attempts,
                type(error).__name__,
                wait,
            )
            time.sleep(wait)
    raise AssertionError("unreachable: the loop returns or raises")  # keeps type checkers happy
