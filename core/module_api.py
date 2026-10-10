"""API for module backends. Authenticated with the module's token; a module only sees its own tickets."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from core.auth import DB, CurrentModule
from core.chat import lock_user
from core.models import Ticket, TicketStatus
from core.registry import ModuleConfig
from core.schemas import NotifyIn, TicketIn, TicketOut, TicketPatch

router = APIRouter(prefix="/module", tags=["module"])


async def _own_ticket(session: DB, module: ModuleConfig, ticket_id: uuid.UUID) -> Ticket:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None or ticket.kind != module.name:
        raise HTTPException(404, "no such ticket")
    return ticket


@router.post("/tickets")
async def create_ticket(body: TicketIn, module: CurrentModule, session: DB) -> TicketOut:
    await lock_user(session, body.user_id)
    ticket = Ticket(user_id=body.user_id, kind=module.name, title=body.title, details=body.details)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return TicketOut.model_validate(ticket)


@router.get("/tickets")
async def list_tickets(
    module: CurrentModule, session: DB, status: TicketStatus | None = None
) -> list[TicketOut]:
    query = select(Ticket).where(Ticket.kind == module.name).order_by(Ticket.created_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    return [TicketOut.model_validate(t) for t in await session.scalars(query.limit(500))]


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: uuid.UUID, module: CurrentModule, session: DB) -> TicketOut:
    return TicketOut.model_validate(await _own_ticket(session, module, ticket_id))


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: uuid.UUID, body: TicketPatch, module: CurrentModule, session: DB
) -> TicketOut:
    ticket = await _own_ticket(session, module, ticket_id)
    if ticket.status == TicketStatus.ARCHIVED:
        raise HTTPException(409, "ticket is archived")
    if body.status:
        ticket.status = TicketStatus(body.status)
        ticket.resolved_at = func.now() if body.status == "resolved" else None
    if body.resolution is not None:
        ticket.resolution = body.resolution
    await session.commit()
    await session.refresh(ticket)
    return TicketOut.model_validate(ticket)


@router.post("/tickets/{ticket_id}/notify")
async def notify(ticket_id: uuid.UUID, body: NotifyIn, module: CurrentModule, session: DB) -> TicketOut:
    """A supplier update for the user. Lands in the chat as a tagged message.

    TODO(webhook): start the agent if idle, or queue the message if a run is active;
    after 24h send the module's WhatsApp template instead.
    """
    ticket = await _own_ticket(session, module, ticket_id)
    if ticket.status not in (TicketStatus.ACTIVE, TicketStatus.AWAITING_USER):
        raise HTTPException(409, f"ticket is {ticket.status}")
    user = await lock_user(session, ticket.user_id)
    user.messages.append(
        {"role": "user", "content": f"[supplier · {module.name} · ticket {ticket.id}] {body.message}"}
    )
    ticket.status = TicketStatus.AWAITING_USER
    await session.commit()
    await session.refresh(ticket)
    return TicketOut.model_validate(ticket)
