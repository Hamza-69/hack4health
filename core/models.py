import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base

# A chat is a list of messages in full LLM API format (role, content, tool calls).
Messages = MutableList.as_mutable(JSONB)


class TicketStatus(enum.StrEnum):
    ACTIVE = "active"
    AWAITING_USER = "awaiting_user"  # supplier is done, waiting for the user to respond
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)  # from core.identity.user_id_for
    messages: Mapped[list[dict]] = mapped_column(
        Messages, default=list, server_default=text("'[]'::jsonb")
    )
    current_ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tickets.id", use_alter=True, ondelete="SET NULL")
    )
    agent_running_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (Index("ix_tickets_user_id_status", "user_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str]  # name of the module that owns this ticket
    title: Mapped[str]
    details: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", values_callable=lambda e: [m.value for m in e]),
        default=TicketStatus.ACTIVE,
    )
    resolution: Mapped[str | None] = mapped_column(Text)  # agent's note on how it ended
    archive_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("archives.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Archive(Base):
    """A pruned slice of a user's chat. Its tickets point here through Ticket.archive_id."""

    __tablename__ = "archives"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    messages: Mapped[list[dict]] = mapped_column(Messages)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
