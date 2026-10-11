"""Admin API for the ministry inbox page, mounted at /api. Every route requires an admin token.

A desk decision (approve, ask for more, decline) is sent to the user through the core's notify:
the agent tells them in their own language, on the app they wrote from.
"""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from h4h import Admin
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import catalog
from app.models import Request
from app.module import module

Session = Annotated[AsyncSession, Depends(module.session)]
CurrentAdmin = Annotated[Admin, Depends(module.admin)]

Action = Literal["approve", "ask", "decline"]
NEXT_STATUS = {"approve": "approved", "ask": "needs_info", "decline": "declined"}
ALLOWED_FROM = {"approve": {"submitted", "needs_info"}, "ask": {"submitted"}, "decline": {"submitted", "needs_info"}}


class DecisionIn(BaseModel):
    message: str = ""


def _summary(r: Request) -> dict:
    s = catalog.get(r.service)
    return {
        "number": r.number,
        "code": r.code,
        "service": r.service,
        "service_title": s["title_en"],
        "service_title_ar": s["title_ar"],
        "patient": r.fields.get("patient_name") or r.fields.get("facility") or "",
        "status": r.status,
        "documents": len(r.documents),
        "created_at": r.created_at,
        "updated_at": r.updated_at,
        "decision_due": r.decision_due,
        "overdue": r.status == "submitted" and r.decision_due < datetime.now(UTC),
    }


def _detail(r: Request) -> dict:
    s = catalog.get(r.service)
    labels = {d["key"]: d for d in s["documents"]}
    received = {d["kind"] for d in r.documents}
    return {
        **_summary(r),
        "desk": s["desk"],
        "desk_contact": s["desk_contact"],
        "how_it_works_today": s["how_it_works_today"],
        "source_urls": s["source_urls"],
        "fields": [{**f, "value": r.fields.get(f["key"], "")} for f in s["fields"]],
        "documents": [
            {**d, "label_en": labels.get(d["kind"], {}).get("label_en", d["kind"]),
             "label_ar": labels.get(d["kind"], {}).get("label_ar", "")}
            for d in r.documents
        ],
        "checklist": [
            {"key": d["key"], "label_en": d["label_en"], "label_ar": d["label_ar"], "required": d["required"],
             "received": d["key"] in received}
            for d in s["documents"]
        ],
        "history": r.history,
    }


def _notice(r: Request, action: Action, message: str) -> str:
    s = catalog.get(r.service)
    note = f" Note from the desk: {message}" if message else ""
    match action:
        case "approve":
            return f"Request {r.code} ({s['title_en']}) was APPROVED by the {s['desk']}.{note} {s['after_approval']}".strip()
        case "ask":
            return f"Request {r.code} ({s['title_en']}): the {s['desk']} needs more before deciding: {message}"
        case "decline":
            return f"Request {r.code} ({s['title_en']}) was DECLINED by the {s['desk']}. Reason: {message}"


@module.api.get("/requests")
async def list_requests(session: Session) -> list[dict]:
    rows = await session.scalars(select(Request).order_by(Request.number.desc()))
    return [_summary(r) for r in rows]


@module.api.get("/requests/{number}")
async def get_request(number: int, session: Session) -> dict:
    r = await session.get(Request, number)
    if r is None:
        raise HTTPException(404, "no such request")
    return _detail(r)


@module.api.post("/requests/{number}/{action}")
async def decide(number: int, action: Action, body: DecisionIn, admin: CurrentAdmin, session: Session) -> dict:
    r = await session.get(Request, number)
    if r is None:
        raise HTTPException(404, "no such request")
    if r.status not in ALLOWED_FROM[action]:
        raise HTTPException(409, f"{r.code} is {r.status}")
    message = body.message.strip()
    if action in ("ask", "decline") and not message:
        raise HTTPException(422, "say what is needed" if action == "ask" else "give a reason")
    await module.core.notify(r.ticket_id, _notice(r, action, message))
    r.status = NEXT_STATUS[action]
    r.history = [*r.history, {"at": datetime.now(UTC).isoformat(), "by": admin.email, "action": NEXT_STATUS[action],
                              "message": message}]
    await session.commit()
    await session.refresh(r)
    return _detail(r)
