"""This module's own tables. They live in its Postgres schema, never in the core's."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, Sequence, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.module import module

FIRST_NUMBER = 501
number_seq = Sequence("report_number_seq", start=FIRST_NUMBER, metadata=module.Base.metadata)


class Report(module.Base):
    """A report that a hospital charged a patient the ministry covers in full. Shown as R-<number>."""

    __tablename__ = "reports"

    number: Mapped[int] = mapped_column(Integer, number_seq, primary_key=True)
    ticket_id: Mapped[uuid.UUID]  # core ticket; no FK across schemas
    user_id: Mapped[uuid.UUID]
    hospital_id: Mapped[str] = mapped_column(String(120))  # cover.Hospital.id, to group reports per hospital
    hospital: Mapped[dict] = mapped_column(JSON)  # the hospital's card when reported
    patient_name: Mapped[str] = mapped_column(Text)
    incident_date: Mapped[str] = mapped_column(String(40))
    amount: Mapped[str] = mapped_column(Text)  # as asked, with its currency
    paid: Mapped[bool]
    situation: Mapped[dict] = mapped_column(JSON)  # {patient_cover, injury}
    rule: Mapped[dict] = mapped_column(JSON)  # what check_bill said when reported: rule, sources
    documents: Mapped[list] = mapped_column(JSON)  # [{kind, url, description, added_at}]
    note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="submitted")  # submitted | needs_info | taken_up | closed
    history: Mapped[list] = mapped_column(JSON, default=list)  # [{at, by, action, message}]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def code(self) -> str:
        return f"R-{self.number}"
