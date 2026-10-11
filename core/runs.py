"""Agent runs: one at a time per user, many users at once.

While a user's run is active (users.agent_running_since set and fresh), only that run writes
users.messages. Anything else that arrives for the user goes to users.queue, and the run pours
the queue in at its next step. At every step the run checks the flag is still the one it set,
then refreshes it; a run that went stale and was replaced stops instead of overwriting the chat.

Runs are asyncio tasks in the core process, at most AGENT_MAX_RUNS at once. State lives in
Postgres, so several core workers can share users; a sweeper restarts runs whose worker died.
"""

import asyncio
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from langchain_core.messages import AIMessage, AnyMessage, convert_to_messages, convert_to_openai_messages
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import agent, db, privacy, tokens
from core.chat import archive_if_done, lock_user
from core.models import User
from core.registry import load_clients

STALE_AFTER = timedelta(minutes=5)  # a run that hasn't stepped for this long counts as crashed
SWEEP_EVERY = 60  # seconds between looks for stale runs
MAX_RUNS = int(os.environ.get("AGENT_MAX_RUNS", "50"))
FALLBACK = "Sorry, something went wrong on our side. Please try again in a moment.\nعذراً، صار في مشكلة عنّا. جرّب كمان شوي."

log = logging.getLogger(__name__)

_slots = asyncio.Semaphore(MAX_RUNS)
_tasks: set[asyncio.Task] = set()


class Superseded(Exception):
    """The run's flag was replaced: it went stale and a newer run took over."""


def _now() -> datetime:
    return datetime.now(UTC)


def is_running(user: User) -> bool:
    return user.agent_running_since is not None and _now() - user.agent_running_since < STALE_AFTER


async def submit(session: AsyncSession, user: User, messages: list[dict], *, prune: bool = False) -> bool:
    """Hand messages to the user's agent and commit. The caller holds the user lock.

    If a run is active, the messages join its queue and this returns True. Otherwise they start
    a run, after anything left in the queue by a crashed run; with `prune`, a finished chat is
    archived first.
    """
    if is_running(user):
        user.queue.extend(messages)
        await session.commit()
        return True
    if prune:
        await archive_if_done(session, user)
    user.messages.extend([*user.queue, *messages])
    user.queue = []
    since = user.agent_running_since = _now()
    await session.commit()
    start(user.id, since)
    return False


def start(user_id: uuid.UUID, since: datetime) -> None:
    """Start the run that owns the flag set to `since`. Call it after committing the flag."""
    task = asyncio.create_task(_run(user_id, since))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def _run(user_id: uuid.UUID, since: datetime) -> None:
    async with _slots:
        run = Run(user_id, since)
        try:
            await run.go()
        except Superseded:
            log.warning("run for user %s was superseded", user_id)
        except Exception:
            log.exception("run for user %s failed", user_id)
            try:
                await run.fail()
            except Exception:
                log.exception("could not release the run for user %s", user_id)


class Run:
    def __init__(self, user_id: uuid.UUID, since: datetime):
        self.user_id = user_id
        self.since = since  # the flag value this run owns
        self.app = self.address = None

    async def go(self) -> None:
        """Run turns until the agent has answered and nothing is queued."""
        async with db.Session() as session:
            user = await session.get(User, self.user_id)
            messages = convert_to_messages(user.messages)
            self.app, self.address = user.app, user.address
        while True:
            ctx = await agent.context(self.user_id, sync=self.save, send=self.send)
            messages = await agent.run_turn(messages, ctx)
            if ctx.erase:  # the user asked to delete their data: the reply is out, now forget the chats
                await privacy.erase_history(self.user_id)
                messages = []
            queued = await self.save(messages, last=True)
            if not queued:
                return
            messages = [*messages, *queued]

    async def save(self, messages: list[AnyMessage], *, last: bool = False) -> list[AnyMessage]:
        """Save the chat and take the queued messages, which are part of it from now on.

        Refreshes the flag; with `last` and nothing queued, clears it instead: the run is over.
        """
        async with db.Session() as session:
            user = await self._lock(session)
            queued = list(user.queue)
            user.messages = [*_to_dicts(messages), *queued]
            user.queue = []
            self.since = user.agent_running_since = None if last and not queued else _now()
            await session.commit()
        return convert_to_messages(queued)

    async def fail(self) -> None:
        """Release the flag after a crash. The chat stays as last saved; the queue waits for the
        next message."""
        async with db.Session() as session:
            try:
                user = await self._lock(session)
            except Superseded:
                return
            user.agent_running_since = None
            await session.commit()
        await self.send(FALLBACK)

    async def _lock(self, session: AsyncSession) -> User:
        user = await lock_user(session, self.user_id)
        if user.agent_running_since != self.since:
            raise Superseded
        return user

    async def send(self, text: str) -> None:
        """POST a reply to the user's client. Failures are logged; the reply stays in the chat."""
        client = load_clients().get(self.app) if self.app else None
        if client is None or not self.address:
            log.warning("no client for user %s (app %r); reply dropped", self.user_id, self.app)
            return
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                response = await http.post(
                    client.messages_url,
                    json={"account_id": self.address, "text": text},
                    headers={"Authorization": f"Bearer {tokens.reply_token(client.app)}"},
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            log.error("reply to user %s via %s failed: %s", self.user_id, client.app, e)


def _to_dicts(messages: list[AnyMessage]) -> list[dict]:
    """The chat as plain chat-completions dicts. Provider extras such as OpenAI's encrypted
    reasoning are left out: they only matter within a turn, and the run keeps them in memory."""
    return convert_to_openai_messages(
        [AIMessage(m.text, tool_calls=m.tool_calls) if isinstance(m, AIMessage) else m for m in messages]
    )


async def sweep() -> None:
    """Restart runs whose flag went stale: the run crashed or its worker died."""
    async with db.Session() as session:
        stale = list(
            await session.scalars(select(User.id).where(User.agent_running_since < _now() - STALE_AFTER))
        )
    for user_id in stale:
        async with db.Session() as session:
            user = await lock_user(session, user_id)
            if user.agent_running_since is None or is_running(user):
                continue  # finished, or another worker restarted it first
            since = user.agent_running_since = _now()
            await session.commit()
        log.warning("restarting stale run for user %s", user_id)
        start(user_id, since)


async def sweep_forever() -> None:
    while True:
        await asyncio.sleep(SWEEP_EVERY)
        try:
            await sweep()
        except Exception:
            log.exception("sweeping stale runs failed")


async def stop_all() -> None:
    """Cancel this process's runs. Their flags go stale and the sweeper restarts them."""
    tasks = list(_tasks)
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
