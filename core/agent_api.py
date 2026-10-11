"""The agent API: chat clients post their users' messages here, authenticated with the client's token."""

from fastapi import APIRouter, HTTPException

from core import runs
from core.auth import DB, CurrentClient
from core.chat import lock_user
from core.identity import normalize_account, user_id_for
from core.schemas import MessagesIn, MessagesOut

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
        session, user, [{"role": "user", "content": text} for text in body.messages], prune=True
    )
    return MessagesOut(user_id=user.id, queued=queued)
