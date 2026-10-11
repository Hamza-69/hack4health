"""Admin API for this module's UI, mounted at /api. Every route requires an admin token."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from h4h import Admin
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import catalog, search_index
from app.ingest import data_dir, ingest
from app.models import Claim, Document, Drug, Facility, FreeMed, Gap, IngestRun, Page, SearchLog, Service
from app.module import module

Session = Annotated[AsyncSession, Depends(module.session)]
CurrentAdmin = Annotated[Admin, Depends(module.admin)]


# Overview and reload


@module.api.get("/overview")
async def overview(session: Session) -> dict:
    async def count(model, *where) -> int:
        return await session.scalar(select(func.count()).select_from(model).where(*where))

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    last = await session.scalar(select(IngestRun).order_by(IngestRun.id.desc()).limit(1))
    data = {
        "services": await count(Service),
        "page_chunks": await count(Page),
        "document_chunks": await count(Document),
        "drugs": await count(Drug),
        "free_list_medicines": await count(FreeMed),
        "facilities": await count(Facility),
    }
    try:
        data |= {f"indexed_{name}": n for name, n in (await search_index.counts()).items()}
    except search_index.SearchUnavailable:
        pass  # the overview still shows the tables
    return {
        "data": data,
        "last_load": last and {"at": last.started_at, "data_date": last.data_date, "by": last.by},
        "data_dir": str(data_dir()),
        "open_gaps": await count(Gap, Gap.status == "open"),
        "searches_7d": await count(SearchLog, SearchLog.created_at >= week_ago),
        "empty_searches_7d": await count(SearchLog, SearchLog.created_at >= week_ago, SearchLog.results == 0),
    }


@module.api.post("/reload")
async def reload(admin: CurrentAdmin) -> dict:
    """Reload the crawled data from the files in sandpit/data/. Logs are kept."""
    try:
        counts = await ingest(by=admin.email)
    except FileNotFoundError as e:
        raise HTTPException(400, f"crawl file missing: {e.filename}") from e
    except search_index.SearchUnavailable as e:
        raise HTTPException(503, str(e)) from e
    catalog.invalidate()
    return counts


# Unanswered questions


class GapOut(BaseModel):
    id: int
    question: str
    reason: str
    status: str
    resolution: str
    created_at: datetime


class GapUpdate(BaseModel):
    status: Literal["open", "resolved"]
    resolution: str = ""


@module.api.get("/gaps")
async def list_gaps(session: Session, status: Literal["open", "resolved"] | None = None) -> list[GapOut]:
    query = select(Gap).order_by(Gap.created_at.desc()).limit(500)
    if status:
        query = query.where(Gap.status == status)
    return [GapOut.model_validate(g, from_attributes=True) for g in await session.scalars(query)]


@module.api.patch("/gaps/{gap_id}")
async def update_gap(gap_id: int, body: GapUpdate, session: Session) -> GapOut:
    gap = await session.get(Gap, gap_id)
    if gap is None:
        raise HTTPException(404, "no such question")
    gap.status, gap.resolution = body.status, body.resolution
    await session.commit()
    await session.refresh(gap)
    return GapOut.model_validate(gap, from_attributes=True)


# Rumours


class ClaimOut(BaseModel):
    """Near-duplicate checks of one claim, with the newest wording, verdict and source."""

    claim: str
    count: int
    verdict: str
    source_url: str | None
    source_date: str | None
    first_seen: datetime
    last_seen: datetime


@module.api.get("/claims")
async def list_claims(session: Session) -> list[ClaimOut]:
    """Forwarded messages and rumours the agent checked, grouped by claim, most recently seen first."""
    groups: dict[str, ClaimOut] = {}
    for c in await session.scalars(select(Claim).order_by(Claim.created_at.desc()).limit(5000)):
        if group := groups.get(c.key):
            group.count += 1
            group.first_seen = c.created_at
        else:
            groups[c.key] = ClaimOut(
                claim=c.claim, count=1, verdict=c.verdict, source_url=c.source_url, source_date=c.source_date,
                first_seen=c.created_at, last_seen=c.created_at,
            )
    return list(groups.values())[:200]


# Searches


class SearchOut(BaseModel):
    tool: str
    query: str
    results: int
    created_at: datetime


@module.api.get("/searches")
async def list_searches(session: Session, empty_only: bool = False) -> list[SearchOut]:
    query = select(SearchLog).order_by(SearchLog.created_at.desc()).limit(200)
    if empty_only:
        query = query.where(SearchLog.results == 0)
    return [SearchOut.model_validate(s, from_attributes=True) for s in await session.scalars(query)]


TOPICS = {
    "search_services": "Services and how to apply",
    "get_service": "Services and how to apply",
    "search_ministry_site": "Coverage and announcements",
    "lookup_drug": "Medicines and prices",
    "find_facilities": "Hospitals, centres and pharmacies",
}


@module.api.get("/insights")
async def insights(session: Session, days: int = 7) -> dict:
    """What people asked in the last `days`: by topic, the most repeated questions, and the ones
    the ministry's data could not answer. Built from the anonymous search log."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = list(await session.scalars(select(SearchLog).where(SearchLog.created_at >= since)))
    by_topic: dict[str, int] = {}
    repeated: dict[str, dict] = {}
    for s in rows:
        topic = TOPICS.get(s.tool, s.tool.replace("_", " "))
        by_topic[topic] = by_topic.get(topic, 0) + 1
        key = " ".join(s.query.lower().split())
        entry = repeated.setdefault(key, {"query": s.query, "topic": topic, "count": 0, "found": 0})
        entry["count"] += 1
        entry["found"] += s.results > 0
    not_found = [e for e in repeated.values() if e["found"] == 0]
    open_gaps = await session.scalar(select(func.count()).select_from(Gap).where(Gap.status == "open"))
    return {
        "days": days,
        "total": len(rows),
        "answered_share": round(sum(s.results > 0 for s in rows) / len(rows), 2) if rows else None,
        "open_unanswered": open_gaps,
        "by_topic": sorted(({"topic": t, "count": c} for t, c in by_topic.items()), key=lambda t: -t["count"]),
        "top": sorted(repeated.values(), key=lambda e: (-e["count"], e["query"]))[:10],
        "not_found": sorted(not_found, key=lambda e: -e["count"])[:10],
    }


# Insights: counts only, never what was asked

KINDS = {  # search_log.tool -> the kind of question
    "search_services": "Services",
    "search_ministry_site": "Ministry site",
    "lookup_drug": "Medicines",
    "find_facilities": "Facilities",
}
MIN_COUNT = 5  # smaller counts are hidden, so no one person's question can be picked out
LEBANON = ZoneInfo("Asia/Beirut")


def shown(n: int) -> int | None:
    """The count, or None (shown as "fewer than 5") when it is under MIN_COUNT."""
    return n if n >= MIN_COUNT else None


@module.api.get("/insights/weekly")
async def weekly_insights(session: Session) -> dict:
    """Questions per day for the last 7 days by kind, the share of searches that found something,
    and the top 5 rumours. Counts under 5 come back as null."""
    today = datetime.now(LEBANON).date()
    days = [today - timedelta(days=n) for n in range(6, -1, -1)]
    since = datetime.combine(days[0], time(), LEBANON)

    def per_day(model, *columns):
        day = func.date(func.timezone(LEBANON.key, model.created_at))
        return select(*columns, day, func.count()).where(model.created_at >= since).group_by(*columns, day)

    counts: dict[str, dict[date, int]] = {kind: {} for kind in [*dict.fromkeys(KINDS.values()), "Unanswered", "Rumours"]}
    for tool, day, n in await session.execute(per_day(SearchLog, SearchLog.tool)):
        if kind := KINDS.get(tool):
            counts[kind][day] = counts[kind].get(day, 0) + n
    for model, kind in ((Gap, "Unanswered"), (Claim, "Rumours")):
        for day, n in await session.execute(per_day(model)):
            counts[kind][day] = n

    total, answered = (await session.execute(
        select(func.count(), func.count().filter(SearchLog.results > 0))
        .where(SearchLog.created_at >= since, SearchLog.tool.in_(KINDS))
    )).one()

    rumours: dict[str, dict] = {}
    claims = select(Claim.key, Claim.claim, Claim.verdict).where(Claim.created_at >= since).order_by(Claim.created_at.desc())
    for key, claim, verdict in await session.execute(claims):
        # the newest wording and verdict; the key is only for grouping and isn't readable
        rumour = rumours.setdefault(key, {"key": key, "claim": claim, "count": 0, "verdict": verdict})
        rumour["count"] += 1
    top = sorted(rumours.values(), key=lambda r: -r["count"])[:5]

    return {
        "days": [d.isoformat() for d in days],
        "kinds": [
            {"kind": kind, "per_day": [shown(c.get(d, 0)) for d in days], "total": shown(sum(c.values()))}
            for kind, c in counts.items()
        ],
        "searches": {
            "answered": shown(answered),
            "unanswered": shown(total - answered),
            "answered_share": round(answered / total, 2) if total >= MIN_COUNT else None,
        },
        "rumours": [r | {"count": shown(r["count"])} for r in top],
    }
