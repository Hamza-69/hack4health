"""MCP tools the agent calls to file requests with ministry desks and follow them up.

Each call carries the user in `_meta`; get it with module.user(ctx). Raise ToolError for failures
the agent should read.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from h4h import ToolError
from mcp.server.mcpserver import Context
from pydantic import BaseModel, Field
from sqlalchemy import select

from app import catalog
from app.models import Request, number_seq
from app.module import module

ServiceKey = Annotated[str, Field(description="Service key from list_services, e.g. 'hospitalisation'")]
Fields = Annotated[
    dict[str, str],
    Field(description="Details by field key from get_requirements, e.g. {'patient_name': 'Ali Haddad'}"),
]


class Document(BaseModel):
    kind: str = Field(description="Document key from get_requirements, e.g. 'medical_report'")
    url: str = Field(description="The url from the photo message '[photo <url>] ...'")
    description: str = Field("", description="What the photo shows, from the photo message")


Documents = Annotated[list[Document], Field(description="The photos received so far, one per document")]


def _now() -> datetime:
    return datetime.now(UTC)


def _documents(docs: list[Document]) -> list[dict]:
    at = _now().isoformat()
    return [{"kind": d.kind, "url": d.url, "description": d.description, "added_at": at} for d in docs]


def _status(r: Request) -> dict:
    service = catalog.get(r.service)
    last = r.history[-1] if r.history else None
    return {
        "request_number": r.code,
        "service": service["title_en"],
        "status": r.status,
        "desk": service["desk"],
        "submitted_at": r.created_at.isoformat() if r.created_at else None,
        "decision_due": r.decision_due.date().isoformat(),
        "last_update": {"at": last["at"], "action": last["action"], "message": last["message"]} if last else None,
    }


async def _own_request(number: str, user_id) -> Request:
    digits = "".join(c for c in number if c.isdigit())
    async with module.db() as session:
        r = await session.get(Request, int(digits)) if digits else None
    if r is None or r.user_id != user_id:
        raise ToolError(f"no request {number} for this user")
    return r


@module.mcp.tool()
async def list_services(ctx: Context) -> list[dict]:
    """The ministry services Wasel can prepare and submit for the user."""
    await module.user(ctx)
    return [
        {"key": s["key"], "title": s["title_en"], "title_ar": s["title_ar"], "summary": s["summary"]}
        for s in catalog.services().values()
    ]


@module.mcp.tool()
async def get_requirements(service: ServiceKey, ctx: Context) -> dict:
    """Who qualifies, the documents (as photos) and details a request needs, the desk that decides
    it, and how long a decision takes."""
    await module.user(ctx)
    s = catalog.get(service)
    return {k: s[k] for k in (
        "key", "title_en", "title_ar", "who_qualifies", "documents", "fields", "desk", "deadline_days",
        "after_approval", "source_urls",
    )}


@module.mcp.tool()
async def check_request(service: ServiceKey, fields: Fields, documents: Documents, ctx: Context) -> dict:
    """Check a request before submitting it: returns the documents and details still missing.
    Submits nothing."""
    await module.user(ctx)
    s = catalog.get(service)
    kinds = {d.kind for d in documents}
    catalog.check_kinds(s, kinds)
    missing = catalog.missing(s, fields, kinds)
    return {"complete": not any(missing.values()), **missing}


@module.mcp.tool()
async def submit_request(service: ServiceKey, fields: Fields, documents: Documents, ctx: Context) -> dict:
    """Submit a complete request to the ministry desk, once the user has confirmed. Returns the
    request number; refuses (and lists what is missing) if anything required is missing."""
    user = await module.user(ctx)
    s = catalog.get(service)
    kinds = {d.kind for d in documents}
    catalog.check_kinds(s, kinds)
    missing = catalog.missing(s, fields, kinds)
    if any(missing.values()):
        return {"submitted": False, **missing}

    async with module.db() as session:
        number = await session.scalar(select(number_seq.next_value()))
        patient = fields.get("patient_name") or fields.get("facility") or ""
        details = "\n".join(f"{f['label_en']}: {fields.get(f['key'], '')}" for f in s["fields"])
        ticket = await module.core.create_ticket(
            user, f"W-{number} · {s['title_en']}" + (f" · {patient}" if patient else ""), details
        )
        r = Request(
            number=number,
            ticket_id=ticket.id,
            user_id=user.id,
            service=service,
            fields={f["key"]: fields.get(f["key"], "") for f in s["fields"]},
            documents=_documents(documents),
            status="submitted",
            history=[{"at": _now().isoformat(), "by": "Wasel", "action": "submitted",
                      "message": "Checked: every required document and detail is present."}],
            decision_due=_now() + timedelta(days=s["deadline_days"]),
        )
        session.add(r)
        await session.commit()
    return {
        "submitted": True,
        "request_number": r.code,
        "desk": s["desk"],
        "decision_due": r.decision_due.date().isoformat(),
        "after_approval": s["after_approval"],
    }


@module.mcp.tool()
async def request_status(
    ctx: Context,
    request_number: Annotated[str | None, Field(description="e.g. 'W-1042'; omit for all the user's requests")] = None,
) -> dict:
    """Status of the user's requests: submitted, needs_info (the desk asked for more), approved or
    declined, with the desk's latest message."""
    user = await module.user(ctx)
    if request_number:
        return {"requests": [_status(await _own_request(request_number, user.id))]}
    async with module.db() as session:
        rows = await session.scalars(
            select(Request).where(Request.user_id == user.id).order_by(Request.number.desc()).limit(10)
        )
        return {"requests": [_status(r) for r in rows]}


@module.mcp.tool()
async def add_documents(
    request_number: Annotated[str, Field(description="e.g. 'W-1042'")],
    documents: Documents,
    ctx: Context,
    note: Annotated[str, Field(description="What the user said about it, if anything")] = "",
) -> dict:
    """Add the documents a desk asked for to a submitted request, and send it back to the desk."""
    user = await module.user(ctx)
    r = await _own_request(request_number, user.id)
    if r.status in ("approved", "declined"):
        raise ToolError(f"{r.code} is already {r.status}")
    catalog.check_kinds(catalog.get(r.service), {d.kind for d in documents})
    async with module.db() as session:
        r = await session.get(Request, r.number)
        r.documents = [*r.documents, *_documents(documents)]
        r.history = [*r.history, {"at": _now().isoformat(), "by": "Wasel", "action": "documents_added",
                                  "message": note or f"{len(documents)} document(s) added"}]
        if r.status == "needs_info":
            r.status = "submitted"
            await module.core.update_ticket(r.ticket_id, status="active")
        await session.commit()
        return _status(r)
