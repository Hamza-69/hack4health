"""Admin API for the Hospital Bills page, mounted at /api. Every route requires an admin token.

The desk's decision on a report (take it up with the hospital, ask for more, close) reaches the user
through the core's notify: the agent tells them in their own language.
"""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from h4h import Admin
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import cover
from app.models import Report
from app.module import module

Session = Annotated[AsyncSession, Depends(module.session)]
CurrentAdmin = Annotated[Admin, Depends(module.admin)]

Action = Literal["take_up", "ask", "close"]
NEXT_STATUS = {"take_up": "taken_up", "ask": "needs_info", "close": "closed"}
ALLOWED_FROM = {"take_up": {"submitted", "needs_info"}, "ask": {"submitted"}, "close": {"submitted", "needs_info"}}
OPEN = {"submitted", "needs_info"}


class DecisionIn(BaseModel):
    message: str = ""


def _summary(r: Report) -> dict:
    return {
        "number": r.number,
        "code": r.code,
        "hospital": r.hospital,
        "patient": r.patient_name,
        "incident_date": r.incident_date,
        "amount": r.amount,
        "paid": r.paid,
        "status": r.status,
        "created_at": r.created_at,
    }


def _detail(r: Report) -> dict:
    return {**_summary(r), "situation": r.situation, "rule": r.rule, "documents": r.documents, "note": r.note,
            "history": r.history}


def _notice(r: Report, action: Action, message: str) -> str:
    about = f"Report {r.code} (charge at {r.hospital['name']})"
    note = f" Note from the desk: {message}" if message else ""
    match action:
        case "take_up":
            return f"{about}: the ministry's Hospitals Service is TAKING IT UP with the hospital.{note}"
        case "ask":
            return f"{about}: the Hospitals Service needs more before acting: {message}"
        case "close":
            return f"{about} was CLOSED by the Hospitals Service. Reason: {message}"


async def _get(session: AsyncSession, number: int) -> Report:
    r = await session.get(Report, number)
    if r is None:
        raise HTTPException(404, "no such report")
    return r


@module.api.get("/reports")
async def list_reports(session: Session) -> list[dict]:
    rows = await session.scalars(select(Report).order_by(Report.number.desc()))
    return [_summary(r) for r in rows]


@module.api.get("/reports/{number}")
async def get_report(number: int, session: Session) -> dict:
    return _detail(await _get(session, number))


@module.api.post("/reports/{number}/{action}")
async def decide(number: int, action: Action, body: DecisionIn, admin: CurrentAdmin, session: Session) -> dict:
    r = await _get(session, number)
    if r.status not in ALLOWED_FROM[action]:
        raise HTTPException(409, f"{r.code} is {r.status}")
    message = body.message.strip()
    if action in ("ask", "close") and not message:
        raise HTTPException(422, "say what is needed" if action == "ask" else "give a reason")
    await module.core.notify(r.ticket_id, _notice(r, action, message))
    r.status = NEXT_STATUS[action]
    r.history = [*r.history, {"at": datetime.now(UTC).isoformat(), "by": admin.email, "action": r.status,
                              "message": message}]
    await session.commit()
    await session.refresh(r)
    return _detail(r)


@module.api.get("/hospitals")
async def by_hospital(session: Session) -> list[dict]:
    """Reports grouped per hospital: the evidence for the ministry's joint follow-up with the hospitals."""
    groups: dict[str, dict] = {}
    for r in await session.scalars(select(Report).order_by(Report.number)):
        g = groups.setdefault(r.hospital_id, {"hospital": r.hospital, "reports": 0, "open": 0, "taken_up": 0,
                                              "amounts": [], "codes": [], "last_at": None})
        g["reports"] += 1
        g["open"] += r.status in OPEN
        g["taken_up"] += r.status == "taken_up"
        g["amounts"].append(r.amount)
        g["codes"].append(r.code)
        g["last_at"] = r.created_at
    return sorted(groups.values(), key=lambda g: (-g["reports"], g["hospital"]["name"]))


@module.api.get("/rules")
async def rules() -> dict:
    """The rules and the hospital list Wasel checks bills against, so the desk can see what it says."""
    data = cover.data()
    return {"timeline": [{**t, **cover.source(t["source"])} for t in data["timeline"]], "list": data["list"],
            "listed": [{"name_ar": h["name_ar"], "kind": h["kind"]} for h in data["hospitals"]]}
