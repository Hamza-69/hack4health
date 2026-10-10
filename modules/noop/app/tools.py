"""MCP tools the agent can call. Each call carries the user in `_meta`; get it with module.user(ctx).

Raise ToolError for failures the agent should read; any other exception is hidden as a crash.
"""

from h4h import ToolError
from mcp.server.mcpserver import Context

from app.models import Answer
from app.module import module


@module.mcp.tool()
async def ping(ctx: Context) -> str:
    """Check that this module is reachable and the call carries a valid user token."""
    await module.user(ctx)
    return "pong"


@module.mcp.tool()
async def open_request(title: str, details: str, ctx: Context) -> dict:
    """Open a request for the user. A supplier answers it from the admin panel."""
    user = await module.user(ctx)
    ticket = await module.core.create_ticket(user.id, title, details)
    return {"ticket_id": str(ticket.id), "status": ticket.status}


@module.mcp.tool()
async def request_status(ticket_id: str, ctx: Context) -> dict:
    """Status of one of the user's requests, with the supplier's answer once there is one."""
    user = await module.user(ctx)
    ticket = await module.core.get_ticket(ticket_id)
    if ticket.user_id != user.id:
        raise ToolError("no such request")
    async with module.db() as session:
        answer = await session.get(Answer, ticket.id)
    return {"status": ticket.status, "answer": answer.text if answer else None}
