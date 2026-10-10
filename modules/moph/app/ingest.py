"""Load the crawl output (data/ at the repo root) into this module's tables.

    uv run python -m app.ingest            # from modules/moph
    MOPH_DATA_DIR=/path/to/data uv run python -m app.ingest

Crawled tables are replaced as a whole. Facts are seeded from current_rules.csv only while the
facts table is empty, so admin edits survive a reload.
"""

import asyncio
import csv
import hashlib
import json
import logging
import os
from pathlib import Path

from sqlalchemy import delete, func, insert, select, text

from app.models import Drug, Facility, Fact, FreeMed, IngestRun, Page, Service
from app.module import module
from app.text import normalize

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

CHUNK_CHARS = 1200
MIN_PAGE_CHARS = 120
# Listing pages that repeat other pages' content.
SKIP_TITLES = {normalize("آخر ألأخبار"), normalize("آخر الأخبار"), "latest news"}


def data_dir() -> Path:
    return Path(os.environ.get("MOPH_DATA_DIR", DEFAULT_DATA_DIR))


def _csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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

    pages, seen = [], set()
    with (root / "raw" / "pages.jsonl").open() as f:
        for line in f:
            p = json.loads(line)
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
        }
        for f in _csv(structured / "facilities_clean.csv")
    ]

    facts = [
        {
            "topic": r["topic"],
            "rule": r["rule"],
            "who_is_eligible": r["who_is_eligible"],
            "where": r["where"],
            "effective_date": r["effective_date"],
            "source_url": r["source_url"],
            "source_date": r["source_date"],
            "confidence": r["confidence"] or "medium",
            "note": r["comment"],
        }
        for r in _csv(structured / "current_rules.csv")
    ]

    data_date = max(s["data"].get("fetched_at") or "" for s in services)[:10]
    return {
        "services": services,
        "pages": pages,
        "drugs": drugs,
        "free_meds": free_meds,
        "facilities": facilities,
        "facts": facts,
        "data_date": data_date,
    }


async def ingest(root: Path | None = None, by: str = "cli") -> dict[str, int]:
    """Replace the crawled tables with the files' content. Returns row counts."""
    rows = await asyncio.to_thread(load_files, root)
    tables = {"services": Service, "pages": Page, "drugs": Drug, "free_meds": FreeMed, "facilities": Facility}
    counts = {}
    async with module.db() as session:
        for name, model in tables.items():
            await session.execute(delete(model))
            for start in range(0, len(rows[name]), 2000):
                await session.execute(insert(model), rows[name][start : start + 2000])
            counts[name] = len(rows[name])
        if not await session.scalar(select(func.count()).select_from(Fact)):
            await session.execute(insert(Fact), rows["facts"])
            counts["facts_seeded"] = len(rows["facts"])
        session.add(IngestRun(counts=counts, data_date=rows["data_date"], by=by))
        await session.commit()
    return counts


async def ensure_schema() -> None:
    """Create the schema and tables (the module's server does this on startup)."""
    async with module.engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{module.name}"'))
        await conn.run_sync(module.Base.metadata.create_all)


async def _main() -> None:
    from app import embeddings
    from app.catalog import get_catalog

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    await ensure_schema()
    counts = await ingest(by="cli")
    print(f"Loaded from {data_dir()}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    if embeddings.enabled():
        await get_catalog()  # embeds new texts now, so the first question is not slow
        print(f"Embeddings ready ({embeddings.MODEL}).")
    else:
        print("OPENAI_API_KEY not set: search will use keywords only.")
    await module.engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
