import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

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
    user_id: uuid.UUID
    title: str
    details: str | None = None


class TicketPatch(BaseModel):
    # Archiving belongs to chat pruning, so modules can't set it.
    status: Literal["active", "awaiting_user", "resolved"] | None = None
    resolution: str | None = None


class NotifyIn(BaseModel):
    message: str
