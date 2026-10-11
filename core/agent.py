"""The agent: a LangGraph loop over one user's live chat. The model answers or calls tools, and
tool results go back to the model, until it answers without calling a tool.

The graph keeps no state of its own. The chat lives in users.messages; the runner (core/runs.py)
loads it, and at every step the graph calls Context.sync to save it and pour in queued messages.
"""

import asyncio
import json
import logging
import os
import re
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from typing import Annotated, TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolCall, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.runtime import Runtime
from mcp_types import CallToolResult, Tool
from sqlalchemy import func, select

from core import db, tools
from core.models import Ticket, TicketStatus

MODEL = os.environ.get("AGENT_MODEL", "openai:gpt-5.6-luna")  # any init_chat_model "provider:model"
MODEL_TIMEOUT = 120  # seconds per model call
TOOL_TIMEOUT = 60  # seconds per tool call
MAX_STEPS = 25  # model and tool steps in one turn
RESOLUTION_NOTES = 5  # resolutions of archived tickets given as background

PROMPT = """\
You are Wasel (واصل), a WhatsApp assistant for the services of Lebanon's Ministry of Public Health. \
You answer questions from what the ministry publishes: its services and how to apply, what it covers \
and for whom, medicine prices, hospitals and health centres, hotlines and announcements. If asked \
who you are, say this in one line; never call yourself anything but Wasel.

Language. Reply in the language, dialect and script of the user's last message, and never mix \
scripts in one reply:
- Arabizi (Arabic in Latin letters and numbers, e.g. "kifak", "3andi", "7ada") → reply fully in \
Lebanese Arabizi, in the same style. Write official names in Arabizi or English too, never in Arabic \
script. Example: "Eh, fik ta3mol talab esteshfa2 3a 7sab el wezara. Lezem: 1. Taqrir tebbe..."
- Lebanese Arabic in Arabic script → Lebanese Arabic in Arabic script.
- Modern Standard Arabic → Modern Standard Arabic. English → English. French → French.
The ministry's content is in Arabic: translate or transliterate it into the user's script.

Messages starting with "[photo <url>]" are photos the user sent, described for you; "[voice note]" \
messages are what the user said, transcribed. The language of a reply follows the user's own words \
(typed or spoken), never the language of a photo description.

Style: short and plain, the way a helpful person texts on WhatsApp. No markdown: no **, #, headings \
or tables; a short numbered list for steps or documents is fine. Links as bare URLs.

Never mention tickets, ticket ids, tools or "resolving" to the user: those are internal.

Each module below gives you tools and says how to use them. Only state what a tool result in this \
chat says; never fill gaps from general knowledge. If nothing here fits the request, say what you \
can help with.

Messages that start with "[supplier · <module> · ticket <id>]" come from the supplier handling \
that ticket, not from the user. Tell the user what changed in your own words. Once the user has \
responded to that update, call resolve_ticket.
"""

RESOLVE_TICKET = {
    "type": "function",
    "function": {
        "name": "resolve_ticket",
        "description": "Close one of the user's tickets that is awaiting_user, once the user has "
        "responded to the supplier's update.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "resolution": {
                    "type": "string",
                    "description": "One line on how it ended, e.g. 'Picked up 2 insulin pens on "
                    "Tuesday'. Later chats see it as background.",
                },
            },
            "required": ["ticket_id", "resolution"],
        },
    },
}

log = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


@dataclass
class Context:
    user_id: uuid.UUID
    system: str
    tools: list[dict]  # OpenAI function schemas
    sync: Callable[[list[AnyMessage]], Awaitable[list[AnyMessage]]]  # save the chat, return queued messages
    send: Callable[[str], Awaitable[None]]  # deliver text to the user


@cache
def get_model() -> BaseChatModel:
    # OpenAI's reasoning models only take function tools on the Responses API.
    extra = {"use_responses_api": True} if MODEL.startswith("openai:") else {}
    return init_chat_model(MODEL, timeout=MODEL_TIMEOUT, max_retries=2, **extra)


async def context(
    user_id: uuid.UUID,
    sync: Callable[[list[AnyMessage]], Awaitable[list[AnyMessage]]],
    send: Callable[[str], Awaitable[None]],
) -> Context:
    """What one turn runs with: the system prompt and tools as of now."""
    modules = await tools.list_modules()
    async with db.Session() as session:
        open_tickets = await session.scalars(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .where(Ticket.status.in_([TicketStatus.ACTIVE, TicketStatus.AWAITING_USER]))
            .order_by(Ticket.created_at)
        )
        archived = await session.scalars(
            select(Ticket)
            .where(Ticket.user_id == user_id, Ticket.status == TicketStatus.ARCHIVED)
            .where(Ticket.resolution.is_not(None))
            .order_by(Ticket.resolved_at.desc())
            .limit(RESOLUTION_NOTES)
        )
        system = _system_prompt(modules, list(open_tickets), list(archived))
    schemas = [RESOLVE_TICKET, *(_schema(tool) for module in modules for tool in module.tools)]
    return Context(user_id, system, schemas, sync, send)


def _system_prompt(modules: list[tools.ModuleTools], open_tickets: list[Ticket], archived: list[Ticket]) -> str:
    parts = [PROMPT, f"Current time: {datetime.now(UTC):%A %Y-%m-%d %H:%M} UTC"]
    parts += [f"## Module {m.name}\n\n{m.instructions}" for m in modules if m.instructions]
    if open_tickets:
        parts.append("## The user's open tickets\n\n" + "\n".join(
            f"- {t.id} · {t.kind} · {t.status} · {t.title}" for t in open_tickets
        ))
    if archived:
        parts.append("## Earlier conversations (resolved)\n\n" + "\n".join(
            f"- {t.resolved_at:%Y-%m-%d} · {t.kind} · {t.title}: {t.resolution}" for t in archived
        ))
    return "\n\n".join(parts)


def _schema(tool: Tool) -> dict:
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description or "", "parameters": tool.input_schema},
    }


async def call_model(state: State, runtime: Runtime[Context]) -> dict:
    ctx = runtime.context
    queued = await ctx.sync(state["messages"])
    model = get_model().bind_tools(ctx.tools)
    messages = [SystemMessage(ctx.system), *state["messages"], *queued]
    if hint := _script_hint(messages):
        messages.append(SystemMessage(hint))
    reply = await model.ainvoke(messages)
    if hint and not reply.tool_calls and _ARABIC.search(reply.text):
        reply = await _rewrite_in_arabizi(reply)
    if reply.text:
        await ctx.send(reply.text)
    return {"messages": [*queued, reply]}


async def call_tools(state: State, runtime: Runtime[Context]) -> dict:
    calls = state["messages"][-1].tool_calls
    return {"messages": await asyncio.gather(*(_call_tool(runtime.context.user_id, c) for c in calls))}


_ARABIC = re.compile(r"[\u0600-\u06ff]")
_ARABIZI = re.compile(
    r"[a-z][2356789][a-z]|\b[2357][a-z]|[a-z][2357]\b|"
    r"\b(shou|shu|kif|kifak|kifik|baddi|badde|bade|bado|eza|iza|3am|ma3|3and|3ande|ya3ne|adde|"
    r"hek|hayde|hayda|ana|enta|enti|lesh|leh|wen|mnih|tayeb|yalla|marhaba|habibi|ktir|kteer)\b"
)


def _script_hint(messages: list[AnyMessage]) -> str | None:
    """A last-moment reminder of the user's script: tool results in Arabic pull the model away from Arabizi."""
    last = next((m for m in reversed(messages) if isinstance(m, HumanMessage) and not m.text.startswith("[photo")), None)
    text = last.text.lower() if last else ""
    if not text or text.startswith("[supplier") or _ARABIC.search(text) or not _ARABIZI.search(text):
        return None
    return (
        "The user writes in Arabizi (Lebanese Arabic in Latin letters). Write your whole reply in Arabizi "
        "with Latin letters and numbers only: not one word in Arabic script, including document names, "
        "offices and quotes from tool results; transliterate them. Links stay as they are."
    )


async def _rewrite_in_arabizi(reply: AIMessage) -> AIMessage:
    """The model still slipped into Arabic script: have it rewrite the answer, keeping everything else."""
    rewrite = await get_model().ainvoke([
        SystemMessage("Rewrite the message fully in Lebanese Arabizi (Latin letters and numbers, e.g. 3, 7, 2). "
                      "Transliterate every word in Arabic script. Keep the meaning, numbers, links and list layout "
                      "exactly. Output only the rewritten message."),
        HumanMessage(reply.text),
    ])
    return AIMessage(rewrite.text, id=reply.id)


def _after_model(state: State) -> str:
    return "tools" if state["messages"][-1].tool_calls else END


async def _call_tool(user_id: uuid.UUID, call: ToolCall) -> ToolMessage:
    """Run one tool call. Any failure goes back to the model as the tool's result."""
    try:
        async with asyncio.timeout(TOOL_TIMEOUT):
            if call["name"] == "resolve_ticket":
                content = await resolve_ticket(user_id, **call["args"])
            else:
                content = _result_text(await tools.call_tool(user_id, call["name"], call["args"]))
    except Exception as e:
        log.warning("tool %s failed: %r", call["name"], e)
        content = f"Error: {e or type(e).__name__}"
    return ToolMessage(content, tool_call_id=call["id"], name=call["name"])


def _result_text(result: CallToolResult) -> str:
    if result.structured_content is not None:
        text = json.dumps(result.structured_content, ensure_ascii=False)
    else:
        text = "\n".join(block.text for block in result.content if block.type == "text")
    return f"Error: {text}" if result.is_error else text


async def resolve_ticket(user_id: uuid.UUID, ticket_id: str, resolution: str) -> str:
    async with db.Session() as session:
        ticket = await session.get(Ticket, uuid.UUID(ticket_id))
        if ticket is None or ticket.user_id != user_id:
            raise ValueError(f"no ticket {ticket_id}")
        if ticket.status != TicketStatus.AWAITING_USER:
            raise ValueError(f"ticket is {ticket.status}; only awaiting_user tickets can be resolved")
        ticket.status, ticket.resolution, ticket.resolved_at = TicketStatus.RESOLVED, resolution, func.now()
        await session.commit()
    return "resolved"


def _build():
    graph = StateGraph(State, context_schema=Context)
    graph.add_node("model", call_model)
    graph.add_node("tools", call_tools)
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", _after_model, ["tools", END])
    graph.add_edge("tools", "model")
    return graph.compile()


graph = _build()


async def run_turn(messages: list[AnyMessage], ctx: Context) -> list[AnyMessage]:
    """Run the agent until it answers without calling a tool. Returns the whole chat."""
    state = await graph.ainvoke({"messages": messages}, context=ctx, config={"recursion_limit": MAX_STEPS})
    return state["messages"]
