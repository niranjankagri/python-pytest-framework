"""Typed contracts of the Notes API responses (pydantic v2).

Every response has the same envelope: success, status, message and data. Parsing a body into
these models checks its shape and types; a missing or wrongly typed field fails the test with
a clear validation error instead of a KeyError somewhere later.
"""

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

# The three categories the API accepts
Category = Literal["Home", "Work", "Personal"]

T = TypeVar("T")


class Contract(BaseModel):
    """Base of all models: unknown extra fields are an error, so the contract stays exact."""

    model_config = ConfigDict(extra="forbid")


class User(Contract):
    """A user as returned by register and profile."""

    id: str
    name: str
    email: str
    # Only present after the profile was updated
    phone: str | None = None
    company: str | None = None


class LoginData(Contract):
    """data of a successful login: the user plus the session token."""

    id: str
    name: str
    email: str
    token: str


class Note(Contract):
    """A note as returned by the notes endpoints."""

    id: str
    title: str
    description: str
    category: Category
    completed: bool
    created_at: datetime
    updated_at: datetime
    user_id: str


class ApiResponse(Contract, Generic[T]):
    """The envelope around every response; data is typed per endpoint, e.g. ApiResponse[Note]."""

    success: bool
    status: int
    message: str
    data: T | None = None
