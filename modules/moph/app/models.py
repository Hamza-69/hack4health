"""This module's own tables. They live in its Postgres schema, never in the core's.

Two kinds:
- Crawled data (services, pages, drugs, free_meds, facilities): replaced as a whole by app.ingest.
- Admin data (facts, gaps, search_log, ingest_runs): kept across ingests. Facts are the
  curated, dated rules the agent treats as the most authoritative source.
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.module import module


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Service(module.Base):
    """An administrative service (procedure) from moph.gov.lb/AdministrativeServices."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)  # the site's service id
    title: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON)  # cleaned record from services_clean.json


class Page(module.Base):
    """A chunk of a site page or news item."""

    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    section: Mapped[str] = mapped_column(String(20))  # page | news | other
    lang: Mapped[str] = mapped_column(String(2))
    date: Mapped[str | None] = mapped_column(String(10))  # YYYY-MM-DD when the site shows one
    chunk: Mapped[int] = mapped_column(Integer)  # position of this chunk in the page
    text: Mapped[str] = mapped_column(Text)


class Drug(module.Base):
    """A row of the National Drugs Database (public price list)."""

    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(primary_key=True)  # the site's drug id
    brand_name: Mapped[str] = mapped_column(Text)
    generic: Mapped[bool] = mapped_column(Boolean)
    ingredients: Mapped[str] = mapped_column(Text)
    dosage: Mapped[str] = mapped_column(Text)
    form: Mapped[str] = mapped_column(Text)
    atc: Mapped[str] = mapped_column(String(20))
    price_lbp: Mapped[float | None] = mapped_column(Float)
    equiv_key: Mapped[str] = mapped_column(Text)  # same molecule, strength and form
    on_free_list: Mapped[bool] = mapped_column(Boolean)
    url: Mapped[str] = mapped_column(Text)


class FreeMed(module.Base):
    """A medicine on one of the lists MoPH distributes for free."""

    __tablename__ = "free_meds"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_type: Mapped[str] = mapped_column(String(40))
    brand_name: Mapped[str] = mapped_column(Text)
    composition: Mapped[str] = mapped_column(Text)
    strength: Mapped[str] = mapped_column(Text)
    form: Mapped[str] = mapped_column(Text)
    therapeutic_class: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)


class Facility(module.Base):
    """A licensed health facility from the Facility Locator."""

    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)  # the site's facility id
    name_en: Mapped[str] = mapped_column(Text)
    name_ar: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(40))
    type_ar: Mapped[str] = mapped_column(Text)
    governorate: Mapped[str] = mapped_column(Text)
    caza_en: Mapped[str] = mapped_column(Text)
    caza_ar: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)


class Fact(module.Base):
    """A curated rule or contact, edited from the admin page. Wins over crawled pages."""

    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(60))
    rule: Mapped[str] = mapped_column(Text)
    who_is_eligible: Mapped[str] = mapped_column(Text, default="")
    where: Mapped[str] = mapped_column(Text, default="")
    effective_date: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    source_date: Mapped[str] = mapped_column(String(10), default="")
    confidence: Mapped[str] = mapped_column(String(10), default="high")  # high | medium | low
    note: Mapped[str] = mapped_column(Text, default="")  # for editors, e.g. what it supersedes
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[str] = mapped_column(Text, default="import")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Gap(module.Base):
    """A question the agent could not answer from our data. Anonymous: no user id."""

    __tablename__ = "gaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="open")  # open | resolved
    resolution: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = _created()


class SearchLog(module.Base):
    """Every search the agent ran, so admins can see what people ask about. Anonymous."""

    __tablename__ = "search_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    tool: Mapped[str] = mapped_column(String(40))
    query: Mapped[str] = mapped_column(Text)
    results: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = _created()


class IngestRun(module.Base):
    __tablename__ = "ingest_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = _created()
    counts: Mapped[dict] = mapped_column(JSON)
    data_date: Mapped[str] = mapped_column(String(10))  # when the crawl files were written
    by: Mapped[str] = mapped_column(Text)
