"""Semantic search on Pinecone, with OpenAI embeddings.

Records are embedded with OpenAI when the data is loaded (app.ingest) and kept in one Pinecone
serverless index, one namespace per kind: `services`, and `site` for pages, news and documents. A
question is embedded the same way and matched by cosine similarity, so a question in English,
Arabic or Arabizi finds the Arabic text that answers it.

A vector's id is `<record id>#<hash>`, the hash covering the model, the embedded text and the
metadata. Syncing a namespace therefore embeds only records that are new or changed and deletes the
ones that are gone: Pinecone is the only store of vectors.

    OPENAI_API_KEY         required (put both keys in modules/moph/.env)
    PINECONE_API_KEY       required
    MOPH_PINECONE_INDEX    default moph
    MOPH_PINECONE_CLOUD    default aws        where a missing index is created; the free plan
    MOPH_PINECONE_REGION   default us-east-1  only has aws us-east-1
    MOPH_EMBEDDING_MODEL   default text-embedding-3-large
    MOPH_EMBEDDING_DIMS    default 1024 (the model's vectors are shortened to this)
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass

from openai import AsyncOpenAI
from pinecone import AsyncPinecone, ServerlessSpec
from pinecone.exceptions import NotFoundException

log = logging.getLogger(__name__)
for _noisy in ("pinecone", "httpx"):  # both log every request at INFO
    logging.getLogger(_noisy).setLevel(logging.WARNING)

INDEX = os.environ.get("MOPH_PINECONE_INDEX", "moph")
CLOUD = os.environ.get("MOPH_PINECONE_CLOUD", "aws")
REGION = os.environ.get("MOPH_PINECONE_REGION", "us-east-1")
MODEL = os.environ.get("MOPH_EMBEDDING_MODEL", "text-embedding-3-large")
DIMS = int(os.environ.get("MOPH_EMBEDDING_DIMS", "1024"))

SERVICES = "services"
SITE = "site"

MAX_CHARS = 6000  # well under the model's 8191-token input limit, even for Arabic
EMBED_BATCH = 96
EMBED_PARALLEL = 4
SYNC_SLICE = 1000  # records embedded and upserted per round, to bound memory
UPSERT_BATCH = 100
DELETE_BATCH = 1000  # Pinecone's limit per delete request


class SearchUnavailable(Exception):
    """Search is not set up, or OpenAI or Pinecone failed. The message is safe to show the agent."""


@dataclass(frozen=True)
class Record:
    id: str  # stable across loads, e.g. "service-6"; ASCII, no "#"
    text: str  # what gets embedded
    metadata: dict  # returned with matches: str, number, bool or list-of-str values


@dataclass(frozen=True)
class Match:
    id: str
    score: float  # cosine similarity
    metadata: dict


_openai: AsyncOpenAI | None = None
_pinecone: AsyncPinecone | None = None
_index = None


def configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY") and os.environ.get("PINECONE_API_KEY"))


def require() -> None:
    if not configured():
        raise SearchUnavailable("search is not set up: OPENAI_API_KEY and PINECONE_API_KEY must be set")


def _clients() -> tuple[AsyncOpenAI, AsyncPinecone]:
    global _openai, _pinecone
    require()
    if _openai is None:
        _openai = AsyncOpenAI(max_retries=4, timeout=60)
        _pinecone = AsyncPinecone()
    return _openai, _pinecone


async def _get_index():
    global _index
    if _index is None:
        _, pc = _clients()
        try:
            _index = await pc.index(name=INDEX)
        except NotFoundException as e:
            raise SearchUnavailable(f"the search index {INDEX!r} does not exist yet; load the data first") from e
    return _index


async def close() -> None:
    global _openai, _pinecone, _index
    if _index is not None:
        await _index.close()
    if _pinecone is not None:
        await _pinecone.close()
    if _openai is not None:
        await _openai.close()
    _openai = _pinecone = _index = None


async def embed(texts: list[str]) -> list[list[float]]:
    client, _ = _clients()
    limit = asyncio.Semaphore(EMBED_PARALLEL)

    async def batch(chunk: list[str]) -> list[list[float]]:
        async with limit:
            response = await client.embeddings.create(model=MODEL, input=chunk, dimensions=DIMS)
        return [d.embedding for d in sorted(response.data, key=lambda d: d.index)]

    texts = [t[:MAX_CHARS] for t in texts]
    batches = await asyncio.gather(*(batch(texts[i : i + EMBED_BATCH]) for i in range(0, len(texts), EMBED_BATCH)))
    return [vector for b in batches for vector in b]


async def ensure_index() -> None:
    """Create the index if it is missing; refuse one whose dimension does not match the model's."""
    _, pc = _clients()
    if not await pc.has_index(INDEX):
        log.info("creating Pinecone index %s (%d dims, %s %s)", INDEX, DIMS, CLOUD, REGION)
        await pc.create_index(
            name=INDEX, dimension=DIMS, metric="cosine", spec=ServerlessSpec(cloud=CLOUD, region=REGION), timeout=300
        )
        return
    description = await pc.describe_index(INDEX)
    if description.dimension != DIMS:
        raise SearchUnavailable(f"index {INDEX!r} has {description.dimension} dimensions, the model gives {DIMS}")


def _vector_id(record: Record) -> str:
    content = json.dumps([MODEL, DIMS, record.text[:MAX_CHARS], record.metadata], ensure_ascii=False, sort_keys=True)
    return f"{record.id}#{hashlib.sha1(content.encode()).hexdigest()[:16]}"


async def _existing_ids(index, namespace: str) -> set[str]:
    ids = set()
    try:
        async for page in index.list(namespace=namespace):
            ids.update(v.id for v in page.vectors)
    except NotFoundException:
        pass  # the namespace does not exist until its first upsert
    return ids


async def sync(namespace: str, records: list[Record], keep_prefix: str | None = None) -> dict[str, int]:
    """Make the namespace hold exactly these records. Only new or changed records are embedded.
    Vectors whose id starts with `keep_prefix` are never deleted (data this machine does not have)."""
    await ensure_index()
    index = await _get_index()
    wanted = {_vector_id(r): r for r in records}
    existing = await _existing_ids(index, namespace)
    new = [vid for vid in wanted if vid not in existing]
    stale = sorted(vid for vid in existing - wanted.keys() if not (keep_prefix and vid.startswith(keep_prefix)))
    for start in range(0, len(new), SYNC_SLICE):
        ids = new[start : start + SYNC_SLICE]
        vectors = await embed([wanted[vid].text for vid in ids])
        await index.upsert(
            vectors=[{"id": vid, "values": v, "metadata": wanted[vid].metadata} for vid, v in zip(ids, vectors)],
            namespace=namespace,
            batch_size=UPSERT_BATCH,
            show_progress=False,
        )
        log.info("%s: embedded and upserted %d/%d", namespace, start + len(ids), len(new))
    # Delete after upserting, so the namespace never goes empty during a reload.
    for start in range(0, len(stale), DELETE_BATCH):
        await index.delete(ids=stale[start : start + DELETE_BATCH], namespace=namespace)
    return {"added": len(new), "removed": len(stale), "total": len(wanted)}


async def query(namespace: str, text: str, top_k: int) -> list[Match]:
    """The records closest in meaning to the text, best first."""
    index = await _get_index()
    try:
        [vector] = await embed([text])
        response = await index.query(vector=vector, top_k=top_k, namespace=namespace, include_metadata=True)
    except Exception as e:
        log.exception("search in %s failed", namespace)
        raise SearchUnavailable(f"search failed ({type(e).__name__}); try again shortly") from e
    return [Match(m.id, m.score, dict(m.metadata or {})) for m in response.matches]


async def counts() -> dict[str, int]:
    """Vectors per namespace. Counts lag writes by a few seconds."""
    index = await _get_index()
    try:
        stats = await index.describe_index_stats()
    except Exception as e:
        raise SearchUnavailable(f"could not read the index ({type(e).__name__})") from e
    return {name: summary.vector_count for name, summary in stats.namespaces.items()}
