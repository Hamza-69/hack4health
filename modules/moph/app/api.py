"""Admin API for this module's UI, mounted at /api. Every route requires an admin token."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from h4h import Admin
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import catalog, search_index
from app.ingest import data_dir, ingest
from app.models import Document, Drug, Facility, FreeMed, Gap, IngestRun, Page, SearchLog, Service
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
