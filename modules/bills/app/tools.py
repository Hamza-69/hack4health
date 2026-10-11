"""MCP tools the agent calls to check a hospital bill against the ministry's rules and report a charge.

Each call carries the user in `_meta`; get it with module.user(ctx). Raise ToolError for failures
the agent should read.
"""

from datetime import UTC, datetime
from typing import Annotated

from h4h import ToolError
from mcp.server.mcpserver import Context
from pydantic import BaseModel, Field
from sqlalchemy import select

from app import cover
from app.models import Report, number_seq
from app.module import module

HospitalName = Annotated[str, Field(description=(
    "The hospital's name exactly as printed on the bill, in its own script (Arabic if it is in Arabic), "
    "or as the user said it. Never a translation."))]
PatientCover = Annotated[cover.PatientCover, Field(description=(
    "The patient's cover: uninsured_lebanese (Lebanese with no NSSF, cooperative, army/security or insurance), "
    "one of the other payers, not_lebanese, or unknown if the user has not said"))]
Injury = Annotated[cover.Injury, Field(description="war or port_blast only if the user said the patient was wounded in it")]


class Document(BaseModel):
    url: str = Field(description="The url from the photo message '[photo <url>] ...'")
    description: str = Field("", description="What the photo shows, from the photo message")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _documents(kind: str, docs: list[Document]) -> list[dict]:
    return [{"kind": kind, "url": d.url, "description": d.description, "added_at": _now()} for d in docs]


@module.mcp.tool()
async def check_bill(
    hospital: HospitalName, ctx: Context, patient_cover: PatientCover = "unknown", injury: Injury = "none"
) -> dict:
    """What the ministry pays at this hospital for this patient and whether the hospital may ask them
    to pay anything, from the ministry's circulars with their dates. Returns need_to_know when it needs
    the hospital or the patient's cover first. Does not judge items or prices on a bill."""
    await module.user(ctx)
    return cover.check(hospital, patient_cover, injury)


@module.mcp.tool()
async def report_charge(
    hospital: HospitalName,
    patient_cover: PatientCover,
    patient_name: Annotated[str, Field(description="The patient's full name")],
    date: Annotated[str, Field(description="Date of the bill or of the admission, YYYY-MM-DD")],
    amount: Annotated[str, Field(description="What the hospital asked the patient to pay, with currency, e.g. '45,000,000 LBP'")],
    paid: Annotated[bool, Field(description="Whether the patient already paid it")],
    bill: Annotated[Document, Field(description="The photo of the bill or of the paper asking for payment")],
    ctx: Context,
    injury: Injury = "none",
    other_documents: Annotated[list[Document], Field(description="Receipts or other papers the user sent about it")] = [],
    note: Annotated[str, Field(description="What happened, in the user's words, if they said more")] = "",
) -> dict:
    """Report to the ministry that a hospital charged a patient it covers in full, once the user has
    confirmed. Only for a no_extra_charge verdict from check_bill; returns the report number."""
    user = await module.user(ctx)
    result = cover.check(hospital, patient_cover, injury)
    if not result["found"]:
        raise ToolError(f"check the bill first; still needed: {'; '.join(result['need_to_know'])}")
    if result["verdict"] != "no_extra_charge":
        raise ToolError(f"nothing to report: the verdict at this hospital is {result['verdict']}. {result['rule']}")
    h = result["hospital"]
    rule = {k: result[k] for k in ("verdict", "condition", "rule", "patient_pays", "limits", "sources") if k in result}

    async with module.db() as session:
        number = await session.scalar(select(number_seq.next_value()))
        ticket = await module.core.create_ticket(
            user,
            f"R-{number} · Charged while covered · {h['name_ar']}",
            f"Hospital: {h['name']}\nDate: {date}\nAmount asked: {amount} ({'paid' if paid else 'not paid'})\n"
            f"Rule: {rule['rule']}",
        )
        r = Report(
            number=number, ticket_id=ticket.id, user_id=user.id, hospital_id=h["id"], hospital=h,
            patient_name=patient_name, incident_date=date, amount=amount, paid=paid,
            situation={"patient_cover": patient_cover, "injury": injury}, rule=rule,
            documents=_documents("bill", [bill]) + _documents("other", other_documents), note=note,
            status="submitted",
            history=[{"at": _now(), "by": "Wasel", "action": "submitted",
                      "message": "Checked against the ministry's rule for this patient at this hospital."}],
        )
        session.add(r)
        await session.commit()
    return {
        "reported": True,
        "report_number": r.code,
        "hospital": h["name"],
        "desk": "Hospitals Service, Directorate of Medical Care",
        "next": "A person at the ministry reviews the report; the user hears back here.",
    }


@module.mcp.tool()
async def add_to_report(
    report_number: Annotated[str, Field(description="e.g. 'R-501'")],
    ctx: Context,
    documents: Annotated[list[Document], Field(description="New photos the ministry asked for")] = [],
    note: Annotated[str, Field(description="What the user said in answer")] = "",
) -> dict:
    """Add what the ministry asked for to one of the user's reports, and send it back for review."""
    user = await module.user(ctx)
    digits = "".join(c for c in report_number if c.isdigit())
    async with module.db() as session:
        r = await session.get(Report, int(digits)) if digits else None
        if r is None or r.user_id != user.id:
            raise ToolError(f"no report {report_number} for this user")
        if r.status in ("taken_up", "closed"):
            raise ToolError(f"{r.code} is already {r.status.replace('_', ' ')}")
        if not (documents or note.strip()):
            raise ToolError("nothing to add")
        r.documents = [*r.documents, *_documents("other", documents)]
        r.history = [*r.history, {"at": _now(), "by": "Wasel", "action": "added",
                                  "message": note or f"{len(documents)} document(s) added"}]
        if r.status == "needs_info":
            r.status = "submitted"
            await module.core.update_ticket(r.ticket_id, status="active")
        await session.commit()
        return {"report_number": r.code, "status": r.status}
