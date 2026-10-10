"""OpenAI embeddings for semantic search, so a question in English, Arabic or Arabizi finds the
Arabic text that answers it.

Vectors are cached in the `embeddings` table by a hash of (model, dimensions, text): a reload or a
fact edit only embeds text that changed. Without OPENAI_API_KEY, `enabled()` is false and search
falls back to keywords only.

    OPENAI_API_KEY           required for semantic search (put it in modules/moph/.env)
    MOPH_EMBEDDING_MODEL     default text-embedding-3-large
    MOPH_EMBEDDING_DIMS      default 1024 (the model's vectors are shortened to this)
"""

import asyncio
import hashlib
import logging
import os

import numpy as np
from openai import AsyncOpenAI
from sqlalchemy import select

from app.models import Embedding
from app.module import module

log = logging.getLogger(__name__)

MODEL = os.environ.get("MOPH_EMBEDDING_MODEL", "text-embedding-3-large")
DIMS = int(os.environ.get("MOPH_EMBEDDING_DIMS", "1024"))
MAX_CHARS = 6000  # well under the model's 8191-token input limit, even for Arabic
BATCH = 96
PARALLEL = 4

_client: AsyncOpenAI | None = None


def enabled() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _openai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(max_retries=4, timeout=60)
    return _client


def _key(text: str) -> str:
    return hashlib.sha1(f"{MODEL}|{DIMS}|{text}".encode()).hexdigest()


async def _embed(texts: list[str]) -> np.ndarray:
    response = await _openai().embeddings.create(model=MODEL, input=texts, dimensions=DIMS)
    vectors = np.array([d.embedding for d in sorted(response.data, key=lambda d: d.index)], dtype=np.float32)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


async def embed_query(text: str) -> np.ndarray | None:
    """The query's unit vector, or None when embeddings are off or the API fails."""
    if not enabled() or not text.strip():
        return None
    try:
        return (await _embed([text[:MAX_CHARS]]))[0]
    except Exception as e:  # search still works on keywords
        log.warning("query embedding failed: %s", e)
        return None


async def embed_documents(texts: list[str]) -> np.ndarray | None:
    """Unit vectors for texts, one row each, from the cache or the API. None when embeddings are off."""
    if not enabled():
        return None
    texts = [t[:MAX_CHARS] for t in texts]
    keys = [_key(t) for t in texts]

    async with module.db() as session:
        cached = {}
        for start in range(0, len(keys), 5000):
            rows = await session.execute(
                select(Embedding.key, Embedding.vector).where(Embedding.key.in_(keys[start : start + 5000]))
            )
            cached.update({k: np.frombuffer(v, dtype=np.float32) for k, v in rows})

    missing = list({k: t for k, t in zip(keys, texts) if k not in cached}.items())
    if missing:
        log.info("embedding %d new texts with %s", len(missing), MODEL)
        limit = asyncio.Semaphore(PARALLEL)

        async def run(batch: list[tuple[str, str]]) -> None:
            async with limit:
                vectors = await _embed([t for _, t in batch])
            async with module.db() as session:
                session.add_all(Embedding(key=k, vector=v.tobytes()) for (k, _), v in zip(batch, vectors))
                await session.commit()
            cached.update({k: v for (k, _), v in zip(batch, vectors)})

        await asyncio.gather(*(run(missing[i : i + BATCH]) for i in range(0, len(missing), BATCH)))

    return np.stack([cached[k] for k in keys]) if keys else np.zeros((0, DIMS), dtype=np.float32)
