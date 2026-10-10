import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class User:
    """The chat user a tool call is for. Comes from the core-signed token in `_meta`."""

    id: uuid.UUID
    # The signed token itself. The core API asks for it back as proof, e.g. to create a ticket.
    token: str = field(repr=False)


@dataclass(frozen=True)
class Admin:
    """The admin panel user calling this module's API. Comes from the admin token."""

    id: uuid.UUID
    email: str
    role: str  # operator | supplier
