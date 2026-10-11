"""What Wasel keeps about a user, and for how long.

- Retention: chats are deleted CHAT_RETENTION_DAYS after they end. An archived chat (its tickets
  closed) goes that long after it was archived; a live chat goes that long after the user's last
  message, unless one of their tickets is still open, because the desk may still need the context.
- Erasure: when a user asks Wasel to delete their data and confirms, the agent calls
  delete_my_data. Once the reply is sent, the run clears the live chat, deletes the archived chats
  and blanks the resolution notes, which are memory of past chats.

Tickets themselves stay either way: they are the user's requests, which the ministry keeps as
records, and their modules hold the documents.
"""

import asyncio
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, exists, select, update

from core import db
from core.chat import lock_user
from core.models import Archive, Ticket, TicketStatus, User

CHAT_RETENTION_DAYS = int(os.environ.get("CHAT_RETENTION_DAYS", "30"))
PURGE_EVERY = 3600  # seconds

log = logging.getLogger(__name__)

_OPEN = (TicketStatus.ACTIVE, TicketStatus.AWAITING_USER)


async def erase_history(user_id: uuid.UUID) -> None:
    """Delete the user's archived chats and the notes kept from them. The run clears the live chat."""
    async with db.Session() as session:
        await session.execute(
            update(Ticket).where(Ticket.user_id == user_id).values(resolution=None, archive_id=None)
        )
        await session.execute(delete(Archive).where(Archive.user_id == user_id))
        await session.commit()


async def purge(now: datetime | None = None) -> tuple[int, int]:
    """Delete chats past retention. Returns (archives deleted, live chats cleared)."""
    cutoff = (now or datetime.now(UTC)) - timedelta(days=CHAT_RETENTION_DAYS)
    async with db.Session() as session:
        archives = await session.execute(delete(Archive).where(Archive.created_at < cutoff))
        await session.commit()
        idle = list(
            await session.scalars(
                select(User.id)
                .where(User.last_active_at < cutoff, User.agent_running_since.is_(None))
                .where(User.messages != [])
                .where(~exists().where(Ticket.user_id == User.id, Ticket.status.in_(_OPEN)))
            )
        )
    for user_id in idle:
        async with db.Session() as session:
            user = await lock_user(session, user_id)
            if user.agent_running_since is None and user.last_active_at < cutoff:
                user.messages, user.current_ticket_id = [], None
            await session.commit()
    return archives.rowcount, len(idle)


async def purge_forever() -> None:
    while True:
        try:
            archived, live = await purge()
            if archived or live:
                log.info("retention: deleted %d archived and %d idle chats", archived, live)
        except Exception:
            log.exception("chat retention failed")
        await asyncio.sleep(PURGE_EVERY)
