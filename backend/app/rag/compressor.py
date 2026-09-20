"""Contextual compression: drop the sentences of a chunk that miss the query.

Keeps citations short enough to render in a card without losing the sentence
that justified the match.

Every chunk in a result set is compressed in one call, so the whole set costs a
single embedding pass instead of one per chunk.
"""

from __future__ import annotations

import numpy as np

from .chunker import split_sentences
from .embedder import embed_documents, embed_query

RELEVANCE_THRESHOLD = 0.3
MIN_SENTENCES = 2


def compress_all(query: str, texts: list[str], *, threshold: float = RELEVANCE_THRESHOLD) -> list[str]:
    """Trim each text to the sentences similar enough to `query`.

    Texts of one sentence pass through untouched; there is nothing to trim and
    no reason to pay to find that out.
    """
    if not texts:
        return []

    sentences_per_text = [split_sentences(text) for text in texts]
    trimmable = [index for index, s in enumerate(sentences_per_text) if len(s) >= MIN_SENTENCES]
    if not trimmable:
        return [text.strip() for text in texts]

    flat = [sentence for index in trimmable for sentence in sentences_per_text[index]]
    similarity = embed_documents(flat) @ embed_query(query)

    results = [text.strip() for text in texts]
    cursor = 0
    for index in trimmable:
        sentences = sentences_per_text[index]
        scores = similarity[cursor : cursor + len(sentences)]
        cursor += len(sentences)
        results[index] = _keep(sentences, scores, threshold)
    return results


def _keep(sentences: list[str], scores: np.ndarray, threshold: float) -> str:
    kept = [sentence for sentence, score in zip(sentences, scores, strict=False) if score >= threshold]
    if not kept:
        # Nothing cleared the bar; keep the single best sentence so the citation
        # is never empty.
        kept = [sentences[int(np.argmax(scores))]]
    return " ".join(kept)
