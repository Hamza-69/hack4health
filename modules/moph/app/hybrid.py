"""Hybrid search: embeddings (meaning, any language) fused with BM25 (exact words and codes).

Semantic search carries the ranking, so an English or Arabizi question finds Arabic text. BM25
adds weight to documents that share the query's exact terms, such as a form number (HEA009) or a
drug name, and keeps search working when embeddings are off.
"""

from dataclasses import dataclass

import numpy as np

from app.bm25 import BM25

RRF_K = 60  # reciprocal rank fusion constant
LEXICAL_WEIGHT = 0.5
LEXICAL_MIN_COVERAGE = 0.5  # a keyword hit counts only if it has half the query's terms
CANDIDATES = 50

STRONG_SIMILARITY = 0.45  # cosine similarity for a "strong" semantic match
STRONG_COVERAGE = 0.5  # share of query terms for a "strong" keyword-only match


@dataclass(frozen=True)
class Hit:
    index: int
    score: float
    match: str  # strong | weak


class HybridIndex:
    def __init__(self, keyword_texts: list[str], semantic_texts: list[str]):
        """keyword_texts feed BM25 (they may repeat titles for weight); semantic_texts get embedded."""
        self.semantic_texts = semantic_texts
        self._bm25 = BM25(keyword_texts)
        self.vectors: np.ndarray | None = None  # set by the loader once embeddings are ready

    def search(self, query: str, query_vector: np.ndarray | None, limit: int) -> list[Hit]:
        lexical = self._bm25.search(query, CANDIDATES)
        if query_vector is None or self.vectors is None or not len(self.vectors):
            return [
                Hit(h.index, h.score, "strong" if h.coverage >= STRONG_COVERAGE else "weak")
                for h in lexical[:limit]
            ]

        similarity = self.vectors @ query_vector
        semantic = np.argsort(-similarity)[:CANDIDATES]
        fused: dict[int, float] = {}
        for rank, i in enumerate(semantic):
            fused[int(i)] = 1 / (RRF_K + rank)
        for rank, h in enumerate(h for h in lexical if h.coverage >= LEXICAL_MIN_COVERAGE):
            fused[h.index] = fused.get(h.index, 0) + LEXICAL_WEIGHT / (RRF_K + rank)
        ranked = sorted(fused, key=fused.get, reverse=True)[:limit]
        return [
            Hit(i, fused[i], "strong" if similarity[i] >= STRONG_SIMILARITY else "weak")
            for i in ranked
        ]
