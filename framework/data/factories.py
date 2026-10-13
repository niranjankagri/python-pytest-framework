"""Builders for unique test data.

Every test creates its own user, so tests never share accounts or depend on each other's data,
and can run in parallel (pytest-xdist) against the shared public demo.
"""

import uuid
from dataclasses import dataclass


def unique_suffix() -> str:
    """Short random suffix that keeps emails and titles unique across runs and workers."""
    return uuid.uuid4().hex[:10]


@dataclass(frozen=True)
class Credentials:
    """A user to register: name, email and password that meet the API's rules."""

    name: str
    email: str
    password: str


def new_user() -> Credentials:
    """A unique user (name 4-30 chars, password 6-30 chars, as the API requires)."""
    suffix = unique_suffix()
    return Credentials(
        name=f"Pytest User {suffix[:6]}",
        email=f"pytest.{suffix}@example.com",
        password=f"Pw-{suffix}",
    )


@dataclass(frozen=True)
class NoteData:
    """The fields of a note to create."""

    title: str
    description: str
    category: str


def new_note(category: str = "Home") -> NoteData:
    """A unique note (title 4-100 chars, description 4-1000 chars)."""
    suffix = unique_suffix()
    return NoteData(
        title=f"Note {suffix}",
        description=f"Created by pytest ({suffix})",
        category=category,
    )
