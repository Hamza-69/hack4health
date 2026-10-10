"""This module's own tables. They live in its Postgres schema, never in the core's."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.module import module


class Answer(module.Base):
    """A supplier's answer to a request."""

    __tablename__ = "answers"

    ticket_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)  # core ticket; no FK across schemas
    text: Mapped[str] = mapped_column(Text)
    answered_by: Mapped[str]  # admin email
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
