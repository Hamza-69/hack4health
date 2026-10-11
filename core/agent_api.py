"""The agent API: chat clients post their users' messages here, authenticated with the client's token."""

import logging
import re

import openai
from fastapi import APIRouter, HTTPException, UploadFile

from core import media, runs
from core.auth import DB, CurrentClient
from core.chat import lock_user
from core.identity import normalize_account, user_id_for
from core.schemas import MediaOut, MessagesIn, MessagesOut

log = logging.getLogger(__name__)

_SUPPLIER_TAG = re.compile(r"\[\s*supplier", re.IGNORECASE)


def _from_user(text: str) -> str:
    """Only the core writes supplier updates (module_api.notify): a tag the user typed is marked as theirs."""
    return _SUPPLIER_TAG.sub("[typed by the user: supplier", text)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/messages", status_code=202)
async def post_messages(body: MessagesIn, client: CurrentClient, session: DB) -> MessagesOut:
    """New messages from one user. Returns at once; the agent's replies are POSTed to the client."""
    try:
        address = normalize_account(client.app, body.account_id)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    user = await lock_user(session, user_id_for(client.app, address))
    user.app, user.address = client.app, address
    queued = await runs.submit(
        session, user, [{"role": "user", "content": _from_user(text)} for text in body.messages], prune=True
    )
    return MessagesOut(user_id=user.id, queued=queued)


@router.post("/media")
async def post_media(file: UploadFile, client: CurrentClient) -> MediaOut:
    """A voice note, photo or PDF from a user, as a message the client sends along with the user's others."""
    data = await file.read(media.MAX_BYTES + 1)
    try:
        return MediaOut(message=await media.to_message(data, file.content_type or ""))
    except media.MediaError as e:
        raise HTTPException(e.status, str(e)) from e
    except openai.OpenAIError as e:
        log.error("media from %s failed: %r", client.app, e)
        raise HTTPException(502, "could not read the file") from e
