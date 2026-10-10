"""Admin API for this module's UI, mounted at /api. Every route requires an admin token."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from h4h import Admin, Ticket
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Answer
from app.module import module

Session = Annotated[AsyncSession, Depends(module.session)]
CurrentAdmin = Annotated[Admin, Depends(module.admin)]


class RequestOut(BaseModel):
    ticket_id: uuid.UUID
    title: str
    details: str | None
    status: str
    created_at: datetime
    answer: str | None
    answered_by: str | None


class AnswerIn(BaseModel):
    text: str


def _out(ticket: Ticket, answer: Answer | None) -> RequestOut:
    return RequestOut(
        ticket_id=ticket.id,
        title=ticket.title,
        details=ticket.details,
        status=ticket.status,
        created_at=ticket.created_at,
        answer=answer.text if answer else None,
        answered_by=answer.answered_by if answer else None,
    )


@module.api.get("/requests")
async def list_requests(session: Session) -> list[RequestOut]:
    # Every admin who can open this module sees every request. To show suppliers only
    # their own, keep a supplier per request and filter on the admin's id here.
    tickets = await module.core.list_tickets()
    answers = {a.ticket_id: a for a in await session.scalars(select(Answer))}
    return [_out(t, answers.get(t.id)) for t in tickets]


@module.api.post("/requests/{ticket_id}/answer")
async def answer_request(
    ticket_id: uuid.UUID, body: AnswerIn, admin: CurrentAdmin, session: Session
) -> RequestOut:
    ticket = await module.core.notify(ticket_id, body.text)
    answer = await session.get(Answer, ticket_id) or Answer(ticket_id=ticket_id)
    answer.text = body.text
    answer.answered_by = admin.email
    answer.answered_at = func.now()
    session.add(answer)
    await session.commit()
    await session.refresh(answer)
    return _out(ticket, answer)
