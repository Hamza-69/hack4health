import json
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from h4h.tokens import TokenType, verify
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage, SystemMessage
from mcp_types import CallToolResult, TextContent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from core import agent, db, privacy, runs, tokens, tools
from core.app import app
from core.auth import get_session
from core.chat import lock_user
from core.models import Archive, Ticket, TicketStatus, User

PHONE = "+96170123456"


@pytest.fixture
async def client(session, monkeypatch):
    app.dependency_overrides[get_session] = lambda: session
    # The runner and the agent open their own sessions; point those at the test database too.
    monkeypatch.setattr(db, "Session", async_sessionmaker(session.bind, expire_on_commit=False))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sent(monkeypatch):
    """Replies the runner sends, instead of POSTing them to the client."""
    sent = []

    async def send(run, text):
        sent.append(text)

    monkeypatch.setattr(runs.Run, "send", send)
    return sent


class FakeModel:
    """Plays back scripted replies and records what the model was shown."""

    def __init__(self, *replies):
        self.replies, self.prompts = list(replies), []

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        self.prompts.append(messages)
        return self.replies.pop(0)


async def no_modules():
    return []


async def post(client, *texts, account=PHONE):
    headers = {"Authorization": f"Bearer {tokens.client_token('wa')}"}
    return await client.post("/agent/messages", headers=headers, json={"account_id": account, "messages": list(texts)})


async def post_user(client, *texts, account=PHONE) -> uuid.UUID:
    return uuid.UUID((await post(client, *texts, account=account)).json()["user_id"])


async def fresh(session, user_id) -> User:
    return await session.scalar(select(User).where(User.id == user_id).execution_options(populate_existing=True))


async def test_only_registered_clients_can_post(client):
    body = {"account_id": PHONE, "messages": ["hi"]}
    for token in (tokens.module_token("testmod"), tokens.client_token("tg")):
        response = await client.post("/agent/messages", headers={"Authorization": f"Bearer {token}"}, json=body)
        assert response.status_code == 401
    assert (await client.post("/agent/messages", json=body)).status_code in (401, 403)


async def test_first_messages_start_a_run_and_later_ones_queue(client, session, started_runs):
    first = await post(client, "hi", "I need insulin", account="961 70 123 456")
    assert (first.status_code, first.json()["queued"]) == (202, False)
    assert (await post(client, "2 pens")).json()["queued"] is True

    user = await fresh(session, uuid.UUID(first.json()["user_id"]))
    assert (user.app, user.address) == ("wa", PHONE)
    assert [m["content"] for m in user.messages] == ["hi", "I need insulin"]
    assert user.queue == [{"role": "user", "content": "2 pens"}]
    assert [user_id for user_id, _ in started_runs] == [user.id]


async def test_run_calls_tools_pours_the_queue_and_finishes(client, session, started_runs, sent, monkeypatch):
    model = FakeModel(
        AIMessage("", tool_calls=[{"id": "c1", "name": "testmod__stock", "args": {"drug": "insulin"}}]),
        AIMessage("Insulin is in stock."),
    )

    async def call_tool(user_id, name, arguments):
        assert (name, arguments) == ("testmod__stock", {"drug": "insulin"})
        await post(client, "2 pens please")  # arrives while the run is busy
        return CallToolResult(content=[TextContent(type="text", text="in stock")])

    monkeypatch.setattr(agent, "get_model", lambda: model)
    monkeypatch.setattr(tools, "list_modules", no_modules)
    monkeypatch.setattr(tools, "call_tool", call_tool)

    user_id = await post_user(client, "do you have insulin?")
    [(_, since)] = started_runs
    await runs.Run(user_id, since).go()

    chat = [m for m in model.prompts[1] if not isinstance(m, SystemMessage)]
    assert chat[-1].content == "2 pens please"  # poured in after the tool result
    user = await fresh(session, user_id)
    assert [(m["role"], m["content"]) for m in user.messages] == [
        ("user", "do you have insulin?"),
        ("assistant", ""),
        ("tool", "in stock"),
        ("user", "2 pens please"),
        ("assistant", "Insulin is in stock."),
    ]
    assert (user.queue, user.agent_running_since) == ([], None)
    assert sent == ["Insulin is in stock."]


async def test_a_replaced_run_stops_without_writing(client, session, started_runs, sent, monkeypatch):
    monkeypatch.setattr(agent, "get_model", lambda: FakeModel(AIMessage("late answer")))
    monkeypatch.setattr(tools, "list_modules", no_modules)
    user_id = await post_user(client, "hi")
    [(_, since)] = started_runs
    user = await lock_user(session, user_id)
    user.agent_running_since = since + runs.STALE_AFTER  # a newer run took over
    await session.commit()

    with pytest.raises(runs.Superseded):
        await runs.Run(user_id, since).go()
    assert [m["content"] for m in (await fresh(session, user_id)).messages] == ["hi"]
    assert sent == []


async def test_messages_after_a_stale_run_start_a_new_one(client, session, started_runs):
    user_id = await post_user(client, "hi")
    await post(client, "still there?")
    user = await lock_user(session, user_id)
    user.agent_running_since -= runs.STALE_AFTER  # the run crashed
    await session.commit()

    assert (await post(client, "hello?")).json()["queued"] is False
    user = await fresh(session, user_id)
    assert [m["content"] for m in user.messages] == ["hi", "still there?", "hello?"]
    assert (user.queue, len(started_runs)) == ([], 2)


async def test_sweeper_restarts_stale_runs_only(client, session, started_runs):
    stale = await post_user(client, "hi")
    await post_user(client, "hi", account="+96171000000")
    user = await lock_user(session, stale)
    user.agent_running_since -= runs.STALE_AFTER
    await session.commit()

    await runs.sweep()
    assert [user_id for user_id, _ in started_runs[2:]] == [stale]


async def test_supplier_update_queues_while_the_agent_runs(client, session, started_runs):
    user_id = await post_user(client, "hi")
    ticket = Ticket(user_id=user_id, kind="testmod", title="Refill")
    session.add(ticket)
    await session.commit()

    response = await client.post(
        f"/module/tickets/{ticket.id}/notify",
        headers={"Authorization": f"Bearer {tokens.module_token('testmod')}"},
        json={"message": "Ready Tue"},
    )
    assert response.json()["status"] == "awaiting_user"
    user = await fresh(session, user_id)
    assert user.queue[-1]["content"] == f"[supplier · testmod · ticket {ticket.id}] Ready Tue"
    assert len(started_runs) == 1


async def test_resolve_ticket_only_closes_the_users_awaiting_tickets(client, session):
    user_id = await post_user(client, "hi")
    awaiting = Ticket(user_id=user_id, kind="testmod", title="Refill", status=TicketStatus.AWAITING_USER)
    active = Ticket(user_id=user_id, kind="testmod", title="Scan")
    session.add_all([awaiting, active])
    await session.commit()

    with pytest.raises(ValueError, match="no ticket"):
        await agent.resolve_ticket(uuid.uuid4(), str(awaiting.id), "Picked up")
    with pytest.raises(ValueError, match="ticket is active"):
        await agent.resolve_ticket(user_id, str(active.id), "Done")
    assert await agent.resolve_ticket(user_id, str(awaiting.id), "Picked up") == "resolved"
    await session.refresh(awaiting)
    assert (awaiting.status, awaiting.resolution) == (TicketStatus.RESOLVED, "Picked up")


async def test_only_a_new_user_gets_the_welcome(client, session, monkeypatch):
    async def modules():
        return [tools.ModuleTools("moph", None, []), tools.ModuleTools("requests", None, [])]

    async def system(user_id):
        return (await agent.context(user_id, sync=None, send=None)).system

    monkeypatch.setattr(tools, "list_modules", modules)
    user_id = await post_user(client, "hi")
    welcome = await system(user_id)
    assert "first time" in welcome and "submit some requests" in welcome and "hospital bill" not in welcome

    user = await lock_user(session, user_id)
    user.messages = [*user.messages, {"role": "assistant", "content": "", "tool_calls": []}]
    await session.commit()
    assert "first time" in await system(user_id)  # a tool call alone is no reply

    user = await lock_user(session, user_id)
    user.messages = [*user.messages, {"role": "assistant", "content": "Hi, I'm Wasel"}]
    await session.commit()
    assert "first time" not in await system(user_id)

    assert "Privacy notice" in welcome and "full page" not in welcome
    monkeypatch.setattr(agent, "PRIVACY_URL", "https://wasel.example/privacy")
    assert "full page: https://wasel.example/privacy" in await system(user_id)

    returning = await post_user(client, "hi again", account="+96171000000")
    session.add(Archive(user_id=returning, messages=[]))
    await session.commit()
    assert "first time" not in await system(returning)


async def test_a_client_greeting_opens_a_new_users_chat_only(client, session):
    headers = {"Authorization": f"Bearer {tokens.client_token('wa')}"}
    body = {"account_id": PHONE, "messages": ["hi"], "greeting": "Hi, I'm Wasel"}
    user_id = uuid.UUID((await client.post("/agent/messages", headers=headers, json=body)).json()["user_id"])
    await client.post("/agent/messages", headers=headers, json=body | {"messages": ["still there?"]})

    user = await fresh(session, user_id)
    assert [(m["role"], m["content"]) for m in user.messages] == [("assistant", "Hi, I'm Wasel"), ("user", "hi")]
    assert user.queue == [{"role": "user", "content": "still there?"}]  # a run is active: no second greeting


async def test_delete_my_data_erases_the_chats_once_the_reply_is_out(client, session, started_runs, sent, monkeypatch):
    model = FakeModel(
        AIMessage("", tool_calls=[{"id": "c1", "name": "delete_my_data", "args": {}}]),
        AIMessage("Done: your conversations with Wasel are deleted."),
    )
    monkeypatch.setattr(agent, "get_model", lambda: model)
    monkeypatch.setattr(tools, "list_modules", no_modules)
    user_id = await post_user(client, "delete my data", "yes")
    session.add(Archive(user_id=user_id, messages=[{"role": "user", "content": "an old chat"}]))
    request = Ticket(user_id=user_id, kind="testmod", title="W-1042", status=TicketStatus.ARCHIVED,
                     resolution="Approved", resolved_at=datetime.now(UTC))
    session.add(request)
    await session.commit()

    [(_, since)] = started_runs
    await runs.Run(user_id, since).go()

    assert sent == ["Done: your conversations with Wasel are deleted."]
    user = await fresh(session, user_id)
    assert (user.messages, user.agent_running_since) == ([], None)
    assert not await session.scalar(select(Archive).where(Archive.user_id == user_id))
    await session.refresh(request)
    assert (request.title, request.resolution) == ("W-1042", None)  # the request stays, the memory goes


async def test_retention_deletes_idle_and_old_chats_but_not_open_requests(client, session):
    idle = await post_user(client, "hi")
    waiting = await post_user(client, "where is my request?", account="+96171000000")
    recent = await post_user(client, "hello", account="+96171000001")
    session.add(Ticket(user_id=waiting, kind="testmod", title="W-1043", status=TicketStatus.AWAITING_USER))
    old = Archive(user_id=recent, messages=[{"role": "user", "content": "long ago"}])
    session.add(old)
    await session.commit()
    later = datetime.now(UTC) + timedelta(days=privacy.CHAT_RETENTION_DAYS, hours=1)
    for user_id in (idle, waiting, recent):
        user = await lock_user(session, user_id)
        user.agent_running_since = None
        if user_id == recent:
            user.last_active_at = later
        await session.commit()

    assert await privacy.purge(now=later) == (1, 1)
    assert (await fresh(session, idle)).messages == []
    assert (await fresh(session, waiting)).messages  # a request is still open
    assert (await fresh(session, recent)).messages  # wrote recently


async def test_replies_go_to_the_client_with_a_reply_token(monkeypatch):
    requests = []
    real = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: requests.append(request) or httpx.Response(200))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=transport, **kw))
    run = runs.Run(uuid.uuid4(), None)
    run.app, run.address = "wa", PHONE

    await run.send("hello")
    [request] = requests
    assert str(request.url) == "http://client.test/messages"
    assert json.loads(request.content) == {"account_id": PHONE, "text": "hello"}
    token = request.headers["Authorization"].removeprefix("Bearer ")
    assert verify(token, tokens._public_key(), audience="client:wa", typ=TokenType.REPLY)["sub"] == "wa"
