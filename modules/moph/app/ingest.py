"""Load the crawl output (sandpit/data/ at the repo root) into this module's tables.

    uv run python -m app.ingest            # from modules/moph
    MOPH_DATA_DIR=/path/to/data uv run python -m app.ingest

Crawled tables are replaced as a whole, then the search index in Pinecone is synced to them
(app.search_index): only new or changed text is embedded.
"""

import asyncio
import csv
import hashlib
import json
import logging
import os
import re
from pathlib import Path

from sqlalchemy import delete, insert, text

from app import search_index
from app.catalog import Catalog
from app.models import Document, Drug, Facility, FreeMed, IngestRun, Page, Service
from app.module import module
from app.search_index import Record
from app.text import normalize

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "sandpit" / "data"

CHUNK_CHARS = 1200
MIN_PAGE_CHARS = 120
MIN_DOCUMENT_CHARS = 200
DOCUMENT_TYPES = {"pdf", "docx", "doc"}  # Excel files are tables (price lists), not text to search
# Listing pages that repeat other pages' content.
SKIP_TITLES = {normalize("آخر ألأخبار"), normalize("آخر الأخبار"), "latest news"}

log = logging.getLogger(__name__)


def data_dir() -> Path:
    return Path(os.environ.get("MOPH_DATA_DIR", DEFAULT_DATA_DIR))


def _csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _given(value: str | None) -> str:
    """A field from a facility page, or "" for the site's placeholders (NA, no, -)."""
    value = (value or "").strip()
    return "" if value.lower() in {"", "na", "n/a", "no", "none", "-", "0"} else value


def _float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def chunk_text(text: str, size: int = CHUNK_CHARS) -> list[str]:
    """Split on line breaks into pieces of about `size` characters. Long lines are cut too."""
    lines = []
    for line in (line.strip() for line in text.splitlines()):
        while len(line) > size * 1.5:
            cut = max(line.rfind(". ", 0, size), line.rfind("، ", 0, size), line.rfind(" ", 0, size))
            cut = cut if cut > size // 2 else size
            lines.append(line[: cut + 1].strip())
            line = line[cut + 1 :].strip()
        if line:
            lines.append(line)
    chunks, current = [], ""
    for line in lines:
        if current and len(current) + len(line) > size:
            chunks.append(current)
            current = ""
        current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def load_files(root: Path | None = None) -> dict[str, list[dict]]:
    """Read the crawl files into rows for each table. No database needed."""
    root = root or data_dir()
    structured = root / "structured"

    services = []
    for s in json.loads((structured / "services_clean.json").read_text()):
        services.append({"id": s["id"], "title": s["title_ar"], "data": s})

    pages, seen, linked_from = [], set(), {}
    with (root / "raw" / "pages.jsonl").open() as f:
        for line in f:
            p = json.loads(line)
            linked_from[p["url"]] = ((p.get("title") or "").strip(), (p.get("date") or None) and p["date"][:10])
            body = (p.get("text") or "").strip()
            if p["section"] == "service" or len(body) < MIN_PAGE_CHARS:
                continue  # services come from services_clean.json
            if normalize(p.get("title") or "").strip() in SKIP_TITLES:
                continue
            digest = hashlib.sha1(normalize(body).encode()).hexdigest()
            if digest in seen:
                continue  # same text on the ar and en side, or under two URLs
            seen.add(digest)
            # The page text starts with its title; drop it, the title is stored on its own.
            title = (p.get("title") or "").strip()
            if title and body.startswith(title):
                body = body[len(title) :].strip()
            for i, piece in enumerate(chunk_text(body)):
                pages.append(
                    {
                        "url": p["url"],
                        "title": title,
                        "section": p["section"],
                        "lang": p["lang"],
                        "date": (p.get("date") or None) and p["date"][:10],
                        "chunk": i,
                        "text": piece,
                    }
                )
    for i, row in enumerate(pages, 1):
        row["id"] = i

    documents = _documents(root, linked_from)
    for i, row in enumerate(documents, 1):
        row["id"] = i

    drugs = [
        {
            "id": int(d["drug_id"]),
            "brand_name": d["brand_name"],
            "generic": d["brand_or_generic"] == "G",
            "ingredients": d["ingredients"],
            "dosage": d["dosage"],
            "form": d["form"],
            "atc": d["atc"],
            "price_lbp": None if d["price_missing"] == "True" else _float(d["price_lbp"]),
            "equiv_key": d["equiv_key"],
            "on_free_list": d["on_moph_free_list"] == "True",
            "url": d["url"],
        }
        for d in _csv(structured / "drugs_clean.csv")
    ]

    free_meds = [
        {
            "id": i,
            "list_type": m["list_type"],
            "brand_name": m["brand_name"],
            "composition": m["generic_composition"],
            "strength": m["strength"],
            "form": m["form"],
            "therapeutic_class": m["therapeutic_class"],
            "source_url": m["source_url"],
        }
        for i, m in enumerate(_csv(structured / "free_meds_unified.csv"), 1)
    ]

    # Addresses come from each facility's own page (the crawler's facility_details step).
    details_csv = structured / "facilities_details.csv"
    details = {d["facility_id"]: d for d in _csv(details_csv)} if details_csv.exists() else {}
    facilities = [
        {
            "id": int(f["facility_id"]),
            "name_en": f["name_en"],
            "name_ar": f["name_ar"],
            "type": f["type"],
            "type_ar": f["type_ar"],
            "governorate": f["governorate"],
            "caza_en": f["caza_en"],
            "caza_ar": f["caza_ar"],
            "phone": f["phone"],
            "url": f["url"],
            "address": _given(details.get(f["facility_id"], {}).get("en:Address")),
        }
        for f in _csv(structured / "facilities_clean.csv")
    ]


    data_date = max(s["data"].get("fetched_at") or "" for s in services)[:10]
    return {
        "services": services,
        "pages": pages,
        "documents": documents,
        "drugs": drugs,
        "free_meds": free_meds,
        "facilities": facilities,
        "data_date": data_date,
    }


def _document_title(local_path: str) -> str:
    """'data/raw/files/Laws/download_file/1397__Karar1167-2015.pdf' -> 'Karar1167-2015'."""
    name = re.sub(r"^\d+__", "", Path(local_path).name)
    name = re.sub(r"\.(pdf|docx?)$", "", name, flags=re.I)
    return re.sub(r"[\s_]+", " ", re.sub(r"\[\d+\]", "", name)).strip()


def _documents(root: Path, linked_from: dict[str, tuple[str, str | None]]) -> list[dict]:
    """Chunks of the text the crawler extracted (or OCR'd) from downloaded files."""
    files = root / "raw" / "files.jsonl"
    if not files.exists():
        return []
    documents, seen = [], set()
    for line in files.open():
        f = json.loads(line)
        text_path = f.get("text_path")
        if f.get("type") not in DOCUMENT_TYPES or not isinstance(text_path, str):
            continue
        path = root.parent / text_path  # paths are relative to the crawler's root, the parent of data/
        if f.get("extract_note") == "scanned_or_no_text" or not path.exists():
            continue
        body = path.read_text(encoding="utf-8", errors="ignore").strip()
        digest = hashlib.sha1(normalize(body).encode()).hexdigest()
        if len(body) < MIN_DOCUMENT_CHARS or digest in seen:
            continue
        seen.add(digest)
        title = _document_title(f["local_path"])
        source_title, source_date = linked_from.get(f["source_page_url"], ("", None))
        year = re.search(r"(?<!\d)(?:19|20)\d{2}(?!\d)", title)
        for i, piece in enumerate(chunk_text(body)):
            documents.append(
                {
                    "url": f["url"],
                    "title": title,
                    "source_url": f["source_page_url"],
                    "source_title": source_title,
                    "date": source_date or (year.group(0) if year else None),
                    "chunk": i,
                    "text": piece,
                }
            )
    return documents


def _key(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:12]


def _metadata(**fields) -> dict:
    return {k: v for k, v in fields.items() if v not in (None, "")}


def index_records(rows: dict) -> dict[str, list[Record]]:
    """What goes into each namespace of the search index."""
    services = [
        Record(f"service-{s['id']}", Catalog.service_text(s["data"]), {"service_id": s["id"], "title": s["title"]})
        for s in rows["services"]
    ]
    site = [
        Record(
            f"page-{_key(p['url'])}-{p['chunk']}",
            f"{p['title']}\n{p['text']}",
            _metadata(kind=p["section"], title=p["title"], url=p["url"], date=p["date"], text=p["text"]),
        )
        for p in rows["pages"]
    ] + [
        Record(
            f"doc-{_key(d['url'])}-{d['chunk']}",
            f"{d['title']}\n{d['source_title']}\n{d['text']}",
            _metadata(kind="document", title=d["title"], url=d["url"], date=d["date"], text=d["text"],
                      found_on=d["source_url"], found_on_title=d["source_title"]),
        )
        for d in rows["documents"]
    ]
    return {search_index.SERVICES: services, search_index.SITE: site}


async def ingest(root: Path | None = None, by: str = "cli") -> dict:
    """Replace the crawled tables with the files' content, then sync the search index to them.
    Returns row counts and, per index namespace, the vectors added, removed and in total."""
    search_index.require()
    await ensure_schema()
    rows = await asyncio.to_thread(load_files, root)
    tables = {"services": Service, "pages": Page, "documents": Document, "drugs": Drug, "free_meds": FreeMed,
              "facilities": Facility}
    counts = {}
    async with module.db() as session:
        for name, model in tables.items():
            await session.execute(delete(model))
            for start in range(0, len(rows[name]), 2000):
                await session.execute(insert(model), rows[name][start : start + 2000])
            counts[name] = len(rows[name])
        await session.commit()
    # The documents' text (downloaded, extracted, OCR'd) lives only on the machine that crawled them.
    # Without it here, keep the documents already in the index instead of deleting them.
    keep = None if rows["documents"] else "doc-"
    if keep:
        log.warning("no document text in %s: keeping the documents already in the search index", root or data_dir())
    for namespace, records in index_records(rows).items():
        counts[f"index_{namespace}"] = await search_index.sync(namespace, records, keep_prefix=keep)
    async with module.db() as session:
        session.add(IngestRun(counts=counts, data_date=rows["data_date"], by=by))
        await session.commit()
    return counts


async def ensure_schema() -> None:
    """Create the schema and tables (the module's server does this on startup)."""
    async with module.engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{module.name}"'))
        await conn.run_sync(module.Base.metadata.create_all)
        # create_all adds no columns to a table that exists
        await conn.execute(text(f'ALTER TABLE "{module.name}".facilities ADD COLUMN IF NOT EXISTS address text '
                                "NOT NULL DEFAULT ''"))


async def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    await ensure_schema()
    try:
        counts = await ingest(by="cli")
    finally:
        await search_index.close()
        await module.engine.dispose()
    print(f"Loaded from {data_dir()}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    asyncio.run(_main())
