"""Semantic chunking: split where the topic changes, not every N characters.

Adjacent sentences are embedded and compared; a similarity drop below the
threshold starts a new chunk. A word budget bounds chunk size so a long
uninterrupted passage still splits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from .embedder import embed_documents

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'\[])")
_SECTION_HEADING = re.compile(r"^\s*(?:[A-Z][A-Z \-/&]{4,}|\d+(?:\.\d+)*\s+[A-Z].{0,80})\s*$")

SIMILARITY_THRESHOLD = 0.5
MAX_WORDS = 220
MIN_WORDS = 40


@dataclass
class Chunk:
    text: str
    section: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]


def split_sections(text: str) -> list[tuple[str, str]]:
    """Group lines under the nearest preceding heading. Returns (heading, body)."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in text.splitlines():
        if _SECTION_HEADING.match(line):
            sections.append((line.strip(), []))
        else:
            sections[-1][1].append(line)
    return [(heading, "\n".join(body).strip()) for heading, body in sections if "".join(body).strip()]


def semantic_chunks(text: str, *, metadata: dict[str, str] | None = None) -> list[Chunk]:
    """Chunk a whole document, respecting section headings then semantic drift."""
    chunks: list[Chunk] = []
    for heading, body in split_sections(text):
        for piece in _chunk_body(body):
            chunks.append(Chunk(text=piece, section=heading, metadata=dict(metadata or {})))
    return chunks


def _chunk_body(body: str) -> list[str]:
    sentences = split_sentences(body)
    if len(sentences) < 2:
        return [body] if body.strip() else []

    vectors = embed_documents(sentences)
    # Normalised vectors, so a dot product is the cosine similarity.
    adjacent_similarity = np.sum(vectors[:-1] * vectors[1:], axis=1)

    pieces: list[str] = []
    current: list[str] = [sentences[0]]
    for sentence, similarity in zip(sentences[1:], adjacent_similarity, strict=False):
        words = sum(len(s.split()) for s in current)
        topic_changed = similarity < SIMILARITY_THRESHOLD and words >= MIN_WORDS
        if topic_changed or words >= MAX_WORDS:
            pieces.append(" ".join(current))
            current = []
        current.append(sentence)
    if current:
        pieces.append(" ".join(current))
    return pieces
