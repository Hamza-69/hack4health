import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from core.models import AdminRole, TicketStatus


class LoginIn(BaseModel):
    email: str
    password: str


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: AdminRole
    modules: list[str]


class LoginOut(BaseModel):
    token: str
    admin: AdminOut


class ModuleOut(BaseModel):
    name: str
    title: str
    ui_url: str


class TokenOut(BaseModel):
    token: str


class AdminTicketOut(BaseModel):
    """A ticket as the admin panel sees it: no user id, no chat."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    title: str
    details: str | None
    status: TicketStatus
    resolution: str | None
    created_at: datetime
    resolved_at: datetime | None


class TicketOut(AdminTicketOut):
    """A ticket as its module sees it."""

    user_id: uuid.UUID


class TicketIn(BaseModel):
    # The user token the module received in `_meta`, not a bare id: proof the user called it.
    user_token: str
    title: str
    details: str | None = None


class TicketPatch(BaseModel):
    # Archiving belongs to chat pruning, so modules can't set it.
    status: Literal["active", "awaiting_user", "resolved"] | None = None
    resolution: str | None = None


class NotifyIn(BaseModel):
    message: str


class MessagesIn(BaseModel):
    account_id: str  # on the client's app: phone number, Telegram chat id or web uuid
    messages: list[str] = Field(min_length=1)  # debounced by the client, oldest first


class MessagesOut(BaseModel):
    user_id: uuid.UUID
    queued: bool  # the user's agent was already running; it picks the messages up at its next step
