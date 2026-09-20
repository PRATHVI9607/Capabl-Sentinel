"""Sparse keyword index. Built once by the ingest script, loaded read-only at runtime."""

from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@dataclass
class BM25Index:
    chunk_ids: list[str]
    _bm25: BM25Okapi

    @classmethod
    def build(cls, chunk_ids: list[str], texts: list[str]) -> BM25Index:
        return cls(chunk_ids=chunk_ids, _bm25=BM25Okapi([tokenize(t) for t in texts] or [[""]]))

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        """Return the top-k (chunk_id, score) pairs, best first.

        Candidates are restricted to documents containing at least one query
        term rather than to a positive score: on a small corpus a term present
        in most documents scores zero, and dropping those would hide real hits.
        """
        tokens = tokenize(query)
        if not tokens or not self.chunk_ids:
            return []
        wanted = set(tokens)
        scores = self._bm25.get_scores(tokens)
        # `doc_freqs` is rank_bm25's per-document term-frequency map.
        matches = [
            (chunk_id, float(score))
            for chunk_id, score, frequencies in zip(
                self.chunk_ids, scores, self._bm25.doc_freqs, strict=False
            )
            if wanted & frequencies.keys()
        ]
        return sorted(matches, key=lambda pair: pair[1], reverse=True)[:k]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pickle.dumps(self))

    @classmethod
    def load(cls, path: Path) -> BM25Index | None:
        if not path.exists():
            return None
        # Only ever loads a file this repo's own ingest script wrote.
        return pickle.loads(path.read_bytes())
