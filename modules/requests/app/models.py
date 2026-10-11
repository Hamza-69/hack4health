"""This module's own tables. They live in its Postgres schema, never in the core's."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, Sequence, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.module import module

FIRST_NUMBER = 1042
number_seq = Sequence("request_number_seq", start=FIRST_NUMBER, metadata=module.Base.metadata)


class Request(module.Base):
    """A request filed with a ministry desk. Shown to users as W-<number>."""

    __tablename__ = "requests"

    number: Mapped[int] = mapped_column(Integer, number_seq, primary_key=True)
    ticket_id: Mapped[uuid.UUID]  # core ticket; no FK across schemas
    user_id: Mapped[uuid.UUID]
    service: Mapped[str] = mapped_column(String(40))  # catalog key
    fields: Mapped[dict] = mapped_column(JSON)  # field key -> value
    documents: Mapped[list] = mapped_column(JSON)  # [{kind, url, description, added_at}]
    status: Mapped[str] = mapped_column(String(20), default="submitted")  # submitted | needs_info | approved | declined
    history: Mapped[list] = mapped_column(JSON, default=list)  # [{at, by, action, message}]
    decision_due: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def code(self) -> str:
        return f"W-{self.number}"
