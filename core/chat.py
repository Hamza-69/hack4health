"""Live chat operations. Run them inside the caller's transaction; nothing here commits."""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Archive, Ticket, TicketStatus, User


async def lock_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    """Get or create the user and lock its row until the transaction ends."""
    await session.execute(insert(User).values(id=user_id).on_conflict_do_nothing())
    return await session.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def archive_if_done(session: AsyncSession, user: User) -> Archive | None:
    """Prune the live chat if it has at least one resolved ticket and none still open.

    Moves the live messages into a new archive, archives the resolved tickets with it,
    and clears the live chat and current ticket. The caller must hold the user lock.
    """
    statuses = set(
        await session.scalars(
            select(Ticket.status)
            .where(Ticket.user_id == user.id, Ticket.status != TicketStatus.ARCHIVED)
            .distinct()
        )
    )
    if statuses != {TicketStatus.RESOLVED}:
        return None

    archive = Archive(user_id=user.id, messages=list(user.messages))
    session.add(archive)
    await session.flush()
    await session.execute(
        update(Ticket)
        .where(Ticket.user_id == user.id, Ticket.status == TicketStatus.RESOLVED)
        .values(status=TicketStatus.ARCHIVED, archive_id=archive.id, archived_at=func.now())
    )
    user.messages = []
    user.current_ticket_id = None
    return archive
