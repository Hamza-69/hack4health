"""Run the eval questions through the real agent and write a report for grading.

    uv run python -m sandpit.eval.run [--only id,id] [--out path] [--concurrency 4]

Each question is one turn for a fresh user, in process: the same agent.context and agent.run_turn
the core uses, with the chat kept in memory instead of users.messages. No users row is needed:
context only reads tickets, and the core creates the row if a module opens a ticket.

Needs the core (modules verify user tokens with its JWKS) and the moph module up: `uv run h4h dev`.
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))  # also works as `python sandpit/eval/run.py`

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage  # noqa: E402

from core import agent, tools  # noqa: E402

QUESTIONS = HERE / "questions.json"
REPORT = HERE / "report.md"
RESULT_PREVIEW = 2000  # characters of each tool result shown in the report


def load_questions(only: str | None) -> list[dict]:
    questions = json.loads(QUESTIONS.read_text())
    if not only:
        return questions
    wanted = [i.strip() for i in only.split(",") if i.strip()]
    unknown = set(wanted) - {q["id"] for q in questions}
    if unknown:
        sys.exit(f"unknown question ids: {', '.join(sorted(unknown))}")
    return [q for q in questions if q["id"] in wanted]


async def preflight() -> list[str]:
    """Check what a run needs before spending model calls. Exits on a blocker; returns warnings."""
    if agent.MODEL.startswith("openai:") and not os.environ.get("OPENAI_API_KEY"):
        sys.exit(f"OPENAI_API_KEY is empty (root .env); the agent model is {agent.MODEL}")
    try:
        ctx = await agent.context(uuid.uuid4(), _no_queue, _discard)
    except Exception as e:
        sys.exit(f"could not build the agent context (is Postgres up, DATABASE_URL right?): {e!r}")
    names = [t["function"]["name"] for t in ctx.tools]
    if not any(n.startswith("moph__") for n in names):
        sys.exit("the moph module is not reachable (see warnings above); start everything with `uv run h4h dev`")
    warnings = []
    contacts = await tools.call_tool(uuid.uuid4(), "moph__get_contacts", {})
    if contacts.is_error:
        sys.exit(f"moph tool calls fail (is the core up on :8000 for its JWKS?): {agent._result_text(contacts)}")
    search = agent._result_text(await tools.call_tool(uuid.uuid4(), "moph__search_services", {"query": "طلب استشفاء على نفقة الوزارة"}))
    if search.startswith("Error:"):
        warnings.append(f"search does not work, so service and site questions will fail: {search[:300]}")
    return warnings


async def _no_queue(messages: list[AnyMessage]) -> list[AnyMessage]:
    return []


async def _discard(text: str) -> None:
    pass


async def ask(question: dict) -> dict:
    """One turn for a fresh user. Keeps what it saw so far if the turn fails."""
    texts: list[tuple[float, str]] = []
    seen: list[AnyMessage] = []
    start = time.monotonic()

    async def sync(messages: list[AnyMessage]) -> list[AnyMessage]:
        seen[:] = messages
        return []

    async def send(text: str) -> None:
        texts.append((time.monotonic() - start, text))

    error = None
    try:
        ctx = await agent.context(uuid.uuid4(), sync, send)
        seen[:] = await agent.run_turn([HumanMessage(question["question"])], ctx)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    seconds = time.monotonic() - start
    result = {
        **question,
        "seconds": seconds,
        "first_text_seconds": texts[0][0] if texts else None,
        "texts": [t for _, t in texts],
        "steps": sum(isinstance(m, AIMessage) for m in seen),
        "calls": tool_calls(seen),
        "error": error,
    }
    print(f"{question['id']}: {seconds:.1f}s, {len(result['calls'])} tool calls" + (f", {error}" if error else ""), flush=True)
    return result


def tool_calls(messages: list[AnyMessage]) -> list[dict]:
    """Each tool call in order, with its result."""
    results = {m.tool_call_id: m.text for m in messages if isinstance(m, ToolMessage)}
    return [
        {"name": call["name"], "args": call["args"], "result": results.get(call["id"])}
        for m in messages if isinstance(m, AIMessage)
        for call in m.tool_calls
    ]


def summarize(result: str | None) -> tuple[str, bool | None]:
    """A short line on a tool result, and whether it found something (None: not a search)."""
    if result is None:
        return "no result", None
    if result.startswith("Error:"):
        return result[:160], False
    try:
        data = json.loads(result)
    except ValueError:
        return result[:80], None
    if not isinstance(data, dict):
        return f"{type(data).__name__}", None
    if "found" in data:
        rows = data.get("results") or []
        strong = sum(r.get("match") == "strong" for r in rows if isinstance(r, dict))
        parts = ["found" if data["found"] else "NOT found", f"{len(rows)} results"]
        if strong:
            parts.append(f"{strong} strong")
        if "total" in data:
            parts.append(f"total {data['total']}")
        if data.get("free_lists"):
            parts.append(f"{len(data['free_lists'])} on free lists")
        if data.get("unknown_area"):
            parts.append(f"unknown area {data['unknown_area']!r}")
        return ", ".join(parts), bool(data["found"])
    if "contacts" in data:
        return f"{len(data['contacts'])} contacts", None
    if "service_id" in data:
        return f"service {data['service_id']}: {data.get('title', '')}"[:120], True
    return ", ".join(list(data)[:6]), None


def short(value, limit: int = 160) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def cell(text: str, limit: int = 70) -> str:
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def quote(text: str) -> str:
    return "\n".join(f"> {line}" if line.strip() else ">" for line in text.splitlines())


def report(results: list[dict], warnings: list[str], modules: list[str]) -> str:
    seconds = sorted(r["seconds"] for r in results if not r["error"])
    errors = sum(bool(r["error"]) for r in results)
    lines = [
        "# Eval report",
        "",
        f"{datetime.now(UTC):%Y-%m-%d %H:%M} UTC · model `{agent.MODEL}` · modules: {', '.join(modules)} · "
        f"{len(results)} questions, {errors} failed",
    ]
    if seconds:
        p90 = seconds[min(len(seconds) - 1, int(len(seconds) * 0.9))]
        lines[-1] += f" · latency median {statistics.median(seconds):.1f}s, p90 {p90:.1f}s, max {seconds[-1]:.1f}s"
    lines += ["", *(f"**Warning:** {w}" for w in warnings), ""]
    lines += [
        "Grade each row against its `expect` note: fill the grade column (ok / partial / wrong).",
        "",
        "| # | question | lang | topic | tools | found | s | answer | grade |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for n, r in enumerate(results, 1):
        found = [summarize(c["result"])[1] for c in r["calls"]]
        searched = [f for f in found if f is not None]
        names = ", ".join(c["name"].partition("__")[2] or c["name"] for c in r["calls"]) or "none"
        answer = "ERROR: " + r["error"] if r["error"] else " / ".join(r["texts"]) or "(no text)"
        lines.append(
            f"| {n} | [{r['id']}](#{r['id']}) | {r['language']} | {r['topic']} | {cell(names, 60)} | "
            f"{f'{sum(searched)}/{len(searched)}' if searched else '-'} | {r['seconds']:.1f} | {cell(answer)} | |"
        )
    for n, r in enumerate(results, 1):
        lines += ["", f'<a id="{r["id"]}"></a>', "", f"## {n}. {r['id']}", ""]
        lines += [f"**Question** ({r['language']}, {r['topic']}):", "", quote(r["question"]), ""]
        lines += [f"**Expect:** {r['expect']}", ""]
        first = f", first text at {r['first_text_seconds']:.1f}s" if r["first_text_seconds"] is not None else ""
        lines += [f"**Answer** ({r['seconds']:.1f}s{first}, {r['steps']} model steps):", ""]
        if r["error"]:
            lines += [f"**Error:** `{r['error']}`", ""]
        for text in r["texts"]:
            lines += [quote(text), ""]
        if not r["texts"] and not r["error"]:
            lines += ["(no text)", ""]
        lines += ["**Tools:**" if r["calls"] else "**Tools:** none", ""]
        for i, c in enumerate(r["calls"], 1):
            summary, _ = summarize(c["result"])
            lines.append(f"{i}. `{c['name']}` `{short(c['args'])}` → {summary}")
        for i, c in enumerate(r["calls"], 1):
            preview = (c["result"] or "")[:RESULT_PREVIEW]
            more = f" (first {RESULT_PREVIEW} of {len(c['result'])} chars)" if len(c["result"] or "") > RESULT_PREVIEW else ""
            lines += ["", f"<details><summary>Result {i}: {c['name']}{more}</summary>", "", "```", preview, "```", "", "</details>"]
    return "\n".join(lines) + "\n"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the eval questions through the agent and write a report.")
    parser.add_argument("--only", help="comma-separated question ids")
    parser.add_argument("--out", type=Path, default=REPORT, help=f"report path (default {REPORT.relative_to(ROOT)})")
    parser.add_argument("--concurrency", type=int, default=4, help="questions at once (default 4)")
    args = parser.parse_args()
    out = args.out.resolve()
    os.chdir(ROOT)  # modules.toml and keys/ are read relative to the working directory

    questions = load_questions(args.only)
    print(f"{len(questions)} questions, model {agent.MODEL}", flush=True)
    warnings = await preflight()
    for w in warnings:
        print(f"warning: {w}", flush=True)
    modules = [m.name for m in await tools.list_modules()]

    slots = asyncio.Semaphore(args.concurrency)

    async def limited(question: dict) -> dict:
        async with slots:
            return await ask(question)

    results = await asyncio.gather(*(limited(q) for q in questions))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report(results, warnings, modules))
    print(f"wrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
