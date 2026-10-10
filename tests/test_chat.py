import uuid

import pytest
from sqlalchemy import select

from core.chat import archive_if_done, lock_user
from core.models import Ticket, TicketStatus

ACTIVE, AWAITING_USER, RESOLVED, ARCHIVED = TicketStatus


async def user_with_tickets(session, *statuses):
    user = await lock_user(session, uuid.uuid4())
    user.messages.append({"role": "user", "content": "hi"})
    tickets = [Ticket(user_id=user.id, kind="test", title="t", status=s) for s in statuses]
    session.add_all(tickets)
    await session.flush()
    return user, tickets


async def test_lock_user_creates_the_user_once(session):
    user_id = uuid.uuid4()
    first = await lock_user(session, user_id)
    second = await lock_user(session, user_id)
    assert first is second
    assert first.messages == []


@pytest.mark.parametrize(
    "statuses",
    [(), (ACTIVE,), (ACTIVE, RESOLVED), (AWAITING_USER, RESOLVED)],
    ids=["no tickets", "active", "active+resolved", "awaiting+resolved"],
)
async def test_keeps_the_chat_until_every_ticket_is_resolved(session, statuses):
    user, _ = await user_with_tickets(session, *statuses)
    assert await archive_if_done(session, user) is None
    assert user.messages == [{"role": "user", "content": "hi"}]


async def test_archives_chat_and_tickets_together(session):
    user, tickets = await user_with_tickets(session, RESOLVED, RESOLVED)
    user.current_ticket_id = tickets[0].id
    await session.flush()

    archive = await archive_if_done(session, user)
    await session.flush()
    await session.refresh(user)

    assert archive.messages == [{"role": "user", "content": "hi"}]
    assert user.messages == []
    assert user.current_ticket_id is None
    rows = (await session.execute(select(Ticket.status, Ticket.archive_id))).all()
    assert rows == [(ARCHIVED, archive.id)] * 2


async def test_next_archive_only_takes_the_new_tickets(session):
    user, _ = await user_with_tickets(session, RESOLVED)
    first = await archive_if_done(session, user)

    user.messages.append({"role": "user", "content": "new issue"})
    session.add(Ticket(user_id=user.id, kind="test", title="t2", status=RESOLVED))
    await session.flush()
    second = await archive_if_done(session, user)

    assert second.messages == [{"role": "user", "content": "new issue"}]
    archive_ids = await session.scalars(
        select(Ticket.archive_id).order_by(Ticket.created_at, Ticket.title)
    )
    assert list(archive_ids) == [first.id, second.id]
