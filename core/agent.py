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

Style: short and plain, the way a helpful person texts on WhatsApp. No markdown: no **, #, headings \
or tables; a short numbered list for steps or documents is fine. Links as bare URLs.

Never mention tickets, ticket ids, tools or "resolving" to the user: those are internal.

Each module below gives you tools and says how to use them. Only state what a tool result in this \
chat says; never fill gaps from general knowledge. If nothing here fits the request, say what you \
can help with.

Messages that start with "[supplier · <module> · ticket <id>]" come from the supplier handling \
that ticket, not from the user. Tell the user what changed in your own words. Once the user has \
responded to that update, call resolve_ticket.

What the user's app adds in square brackets. The language of a reply follows the user's own words \
(typed or spoken), never the language of a description:
- "[voice note] <transcript>": the user spoke this. Treat it as typed, and reply in the language \
and script they would write it in.
- "[photo <link>] <description>" or "[document <link>] <description>": the user sent a photo or \
PDF. The description is automatic and can be wrong; if it matters, ask. Never diagnose or judge \
anything medical from a photo. When a tool takes a document, pass its link.
- "[location: <place or coordinates>]": the user shared a location. If it is only coordinates, ask \
which town or area they are in.
- "[... can't be opened]" or "[... could not be read]": say what you can read (text, voice notes, \
photos, PDFs) and ask them to send it that way.
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
    user = _user_words(messages)
    if script := _script(user):
        messages.append(SystemMessage(_HINTS[script]))
    reply = await model.ainvoke(messages)
    if script and not reply.tool_calls and _wrong_script(script, reply.text):
        log.warning("reply for user %s came out of the user's script (%s); rewriting", ctx.user_id, script)
        reply = await _rewrite(reply, script, user)
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


_LATIN = re.compile(r"[A-Za-z\u00c0-\u024f]")
_URL = re.compile(r"https?://\S+")
_TAGGED = ("[supplier", "[photo", "[document", "[location", "[file", "[video", "[contact")

# Tool results are mostly Arabic and photo descriptions English, and both pull the model away from
# the user's language. A last-moment reminder, then a rewrite if the reply still came out wrong.
_HINTS = {
    "arabizi": "The user writes in Arabizi (Lebanese Arabic in Latin letters). Write your whole reply in Arabizi "
    "with Latin letters and numbers only: not one word in Arabic script, including document names, "
    "offices and quotes from tool results; transliterate them. Links stay as they are.",
    "arabic": "The user writes in Arabic script. Write your whole reply in Arabic script, in their dialect "
    "(Lebanese if they write Lebanese), even when tool results or photo descriptions are in English. "
    "Links and numbers stay as they are.",
    "latin": "The user writes in a language with Latin letters (English or French, not Arabizi). Write your "
    "whole reply in that language, even though tool results are in Arabic. An Arabic document or office "
    "name may follow its translation in brackets. Links stay as they are.",
}
_REWRITES = {
    "arabizi": "Rewrite the message fully in Lebanese Arabizi (Latin letters and numbers, e.g. 3, 7, 2). "
    "Transliterate every word in Arabic script.",
    "arabic": "Rewrite the message fully in Arabic script, in the dialect of this message from the user: {user}",
    "latin": "Rewrite the message fully in the language of this message from the user: {user}\n"
    "Arabic document or office names may stay only in brackets after their translation.",
}


def _user_words(messages: list[AnyMessage]) -> str:
    """The last thing the user wrote or said: not supplier updates, links or media descriptions."""
    texts = (m.text.removeprefix("[voice note]").strip() for m in reversed(messages) if isinstance(m, HumanMessage))
    return next((t for t in texts if t and not t.startswith(_TAGGED) and "could not be read]" not in t), "")


def _script(text: str) -> str | None:
    """arabic, arabizi or latin: how the user writes."""
    if _ARABIC.search(text):
        return "arabic"
    if _ARABIZI.search(text.lower()):
        return "arabizi"
    return "latin" if _LATIN.search(text) else None


def _wrong_script(script: str, reply: str) -> bool:
    text = _URL.sub("", reply)
    arabic, latin = len(_ARABIC.findall(text)), len(_LATIN.findall(text))
    match script:
        case "arabizi":
            return arabic > 0
        case "arabic":
            return latin > arabic
        case _:
            return arabic > latin


async def _rewrite(reply: AIMessage, script: str, user: str) -> AIMessage:
    """The model still slipped out of the user's script: have it rewrite the answer, keeping everything else."""
    instruction = _REWRITES[script].format(user=json.dumps(user[:300], ensure_ascii=False))
    rewrite = await get_model().ainvoke([
        SystemMessage(f"{instruction}\nKeep the meaning, numbers, links and list layout exactly. "
                      "Output only the rewritten message."),
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
