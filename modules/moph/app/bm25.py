"""A small in-memory BM25 index. The corpus is a few thousand documents, so this is instant."""

import math
from collections import Counter, defaultdict
from dataclasses import dataclass

from app.text import tokens

K1 = 1.5
B = 0.75


@dataclass(frozen=True)
class Hit:
    index: int  # position of the document in the list given to BM25()
    score: float
    coverage: float  # share of the query's distinct terms found in the document


class BM25:
    def __init__(self, docs: list[str]):
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self._lengths = []
        for i, doc in enumerate(docs):
            counts = Counter(tokens(doc))
            self._lengths.append(sum(counts.values()))
            for term, tf in counts.items():
                self._postings[term].append((i, tf))
        self._n = len(docs)
        self._avg = (sum(self._lengths) / self._n) if self._n else 0

    def search(self, query: str, limit: int = 5) -> list[Hit]:
        terms = list(dict.fromkeys(tokens(query)))
        if not terms or not self._n:
            return []
        scores: dict[int, float] = defaultdict(float)
        matched: dict[int, int] = defaultdict(int)
        for term in terms:
            postings = self._postings.get(term)
            if not postings:
                continue
            idf = math.log(1 + (self._n - len(postings) + 0.5) / (len(postings) + 0.5))
            for i, tf in postings:
                norm = tf * (K1 + 1) / (tf + K1 * (1 - B + B * self._lengths[i] / self._avg))
                scores[i] += idf * norm
                matched[i] += 1
        # Documents that contain more of the query's terms win over ones that hit one rare term.
        final = {i: s * (1 + matched[i] / len(terms)) for i, s in scores.items()}
        ranked = sorted(final, key=final.get, reverse=True)[:limit]
        return [Hit(i, final[i], matched[i] / len(terms)) for i in ranked]
