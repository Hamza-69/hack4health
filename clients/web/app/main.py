"""Web chat client: a page to talk to the agent, and the client side of the agent API.

The browser posts each message here. After DEBOUNCE_SECONDS without a new one, the batch goes to
the core's POST /agent/messages with this client's token. The core POSTs the agent's replies to
/messages with a reply token, and they reach the browser as server-sent events.

Users are browsers: each keeps a random uuid as its web account id. State is in memory; replies
for a browser that is not connected wait here until it reconnects.
"""

import asyncio
import os
import uuid
from collections import defaultdict
from collections.abc import AsyncIterable
from pathlib import Path
from typing import Annotated

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.sse import EventSourceResponse
from h4h.tokens import TokenType, verify
from pydantic import BaseModel

load_dotenv(".env")  # CLIENT_TOKEN, written by `uv run h4h init`
CORE_URL = os.environ.get("CORE_URL", "http://localhost:8000")
CLIENT_TOKEN = os.environ.get("CLIENT_TOKEN")
DEBOUNCE = float(os.environ.get("DEBOUNCE_SECONDS", "1.5"))
AUDIENCE = "client:web"
PAGE = Path(__file__).parent / "static" / "index.html"

app = FastAPI(title="hack4health web client")
jwks = jwt.PyJWKClient(f"{CORE_URL}/.well-known/jwks.json")

pending: dict[str, list[str]] = defaultdict(list)  # messages waiting out the debounce
timers: dict[str, asyncio.Task] = {}
streams: dict[str, set[asyncio.Queue]] = defaultdict(set)  # open event streams per account
held: dict[str, list[dict]] = defaultdict(list)  # replies for accounts with no open stream


class SendIn(BaseModel):
    account_id: str
    text: str


class ReplyIn(BaseModel):
    account_id: str
    text: str


def _account(raw: str) -> str:
    try:
        return str(uuid.UUID(raw))
    except ValueError as e:
        raise HTTPException(422, "account_id must be a uuid") from e


def _push(account_id: str, event: dict, *, hold: bool = False) -> None:
    if streams.get(account_id):
        for queue in streams[account_id]:
            queue.put_nowait(event)
    elif hold:
        held[account_id].append(event)


@app.get("/", include_in_schema=False)
def page() -> FileResponse:
    return FileResponse(PAGE)


@app.post("/api/send", status_code=202)
async def send(body: SendIn) -> None:
    """One message from the browser. It waits out the debounce with any that follow it."""
    account_id = _account(body.account_id)
    pending[account_id].append(body.text)
    if timer := timers.get(account_id):
        timer.cancel()
    timers[account_id] = asyncio.create_task(_flush_later(account_id))


async def _flush_later(account_id: str) -> None:
    await asyncio.sleep(DEBOUNCE)
    # Taken before the first await, so a newer message starts a new batch instead of cancelling this one.
    texts = pending.pop(account_id)
    del timers[account_id]
    if not CLIENT_TOKEN:
        _push(account_id, {"type": "error", "text": "CLIENT_TOKEN is missing: run `uv run h4h init`."})
        return
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            response = await http.post(
                f"{CORE_URL}/agent/messages",
                headers={"Authorization": f"Bearer {CLIENT_TOKEN}"},
                json={"account_id": account_id, "messages": texts},
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        _push(account_id, {"type": "error", "text": f"The core refused the messages ({e.response.status_code}): {e.response.text}"})
        return
    except httpx.HTTPError as e:
        _push(account_id, {"type": "error", "text": f"Could not reach the core at {CORE_URL}: {e!r}"})
        return
    _push(account_id, {"type": "delivered", "count": len(texts), "queued": response.json()["queued"]})


@app.get("/api/events", response_class=EventSourceResponse)
async def events(account_id: str) -> AsyncIterable[dict]:
    """The browser's stream: replies, plus delivery and error notices for its messages."""
    account_id = _account(account_id)
    queue: asyncio.Queue[dict] = asyncio.Queue()
    for event in held.pop(account_id, []):
        queue.put_nowait(event)
    streams[account_id].add(queue)
    try:
        while True:
            yield await queue.get()
    finally:
        streams[account_id].discard(queue)


bearer = HTTPBearer()


@app.post("/messages")
async def reply(body: ReplyIn, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]) -> None:
    """A reply from the agent, POSTed by the core with a reply token."""
    token = credentials.credentials
    try:
        key = await asyncio.to_thread(jwks.get_signing_key_from_jwt, token)
        verify(token, key.key, audience=AUDIENCE, typ=TokenType.REPLY)
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"invalid reply token: {e}") from e
    _push(_account(body.account_id), {"type": "reply", "text": body.text}, hold=True)
