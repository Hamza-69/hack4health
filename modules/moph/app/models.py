"""This module's own tables. They live in its Postgres schema, never in the core's.

Two kinds:
- Crawled data (services, pages, documents, drugs, free_meds, facilities): replaced as a whole by
  app.ingest, which also syncs the search index in Pinecone (app.search_index).
- Admin data (gaps, claims, search_log, ingest_runs): kept across ingests.
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


class Document(module.Base):
    """A chunk of the text of a file linked from the site: a law, decision, circular, guide or report."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text)  # the file
    title: Mapped[str] = mapped_column(Text)  # from the file name
    source_url: Mapped[str] = mapped_column(Text)  # the page that links to it
    source_title: Mapped[str] = mapped_column(Text)
    date: Mapped[str | None] = mapped_column(String(10))  # the linking page's date, else the year in the name
    chunk: Mapped[int] = mapped_column(Integer)
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
    address: Mapped[str] = mapped_column(Text, default="")  # in Arabic, from the facility's own page


class Gap(module.Base):
    """A question the agent could not answer from our data. Anonymous: no user id."""

    __tablename__ = "gaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(10), default="open")  # open | resolved
    resolution: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = _created()


class Claim(module.Base):
    """A forwarded message or rumour the agent checked against what the ministry published. Anonymous."""

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim: Mapped[str] = mapped_column(Text)
    key: Mapped[str] = mapped_column(Text, index=True)  # shared by near-duplicate claims (app.text.claim_key)
    verdict: Mapped[str] = mapped_column(String(15))  # confirmed | contradicted | not_found
    source_url: Mapped[str | None] = mapped_column(Text)  # the official statement given to the user
    source_date: Mapped[str | None] = mapped_column(Text)
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
