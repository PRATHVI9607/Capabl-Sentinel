"""Test doubles for the two boundaries that would otherwise need the network.

Everything between them -- routing, parsing, retrieval, fusion, scoring,
synthesis, persistence, streaming -- runs for real.
"""

from __future__ import annotations

import zlib
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from pydantic import BaseModel

from app.models import SeverityTier
from app.rag.bm25_index import tokenize
from app.rag.embedder import EMBEDDING_DIM


# --------------------------------------------------------------------------
# Embedding
# --------------------------------------------------------------------------
class HashingEncoder:
    """Deterministic bag-of-words embedder shaped like a fastembed model.

    Documents sharing vocabulary land close together, which is all the
    retrieval layer needs in order to be exercised honestly. It avoids a model
    download in CI.
    """

    def embed(self, texts: Sequence[str], **_: object) -> Iterator[np.ndarray]:
        return iter(self._vectors(list(texts)))

    def query_embed(self, text: str, **_: object) -> Iterator[np.ndarray]:
        return iter(self._vectors([text]))

    @staticmethod
    def _vectors(batch: list[str]) -> np.ndarray:
        vectors = np.zeros((len(batch), EMBEDDING_DIM), dtype=np.float32)
        for row, text in enumerate(batch):
            for token in tokenize(text):
                vectors[row, zlib.crc32(token.encode()) % EMBEDDING_DIM] += 1.0
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.where(norms == 0, 1.0, norms)


# --------------------------------------------------------------------------
# LLM
# --------------------------------------------------------------------------
@dataclass
class _Message:
    content: str


class _StructuredBinding:
    def __init__(self, schema: type[BaseModel], overrides: dict[str, dict]) -> None:
        self._schema = schema
        self._overrides = overrides

    async def ainvoke(self, _messages: list) -> BaseModel:
        return self._schema(**self._overrides.get(self._schema.__name__, {}))


class FakeLLM:
    """Answers with fixed, schema-valid values instead of calling a provider."""

    def __init__(self, overrides: dict[str, dict], text: str) -> None:
        self._overrides = overrides
        self._text = text

    def with_structured_output(self, schema: type[BaseModel]) -> _StructuredBinding:
        return _StructuredBinding(schema, self._overrides)

    async def ainvoke(self, _messages: list) -> _Message:
        return _Message(content=self._text)


class FailingLLM:
    """Every call raises, to exercise the provider-fallback path."""

    def __init__(self, error: Exception | None = None) -> None:
        self._error = error or RuntimeError("provider unavailable")

    def with_structured_output(self, _schema: type[BaseModel]) -> FailingLLM:
        return self

    async def ainvoke(self, _messages: list) -> Any:
        raise self._error


# Values the pipeline's structured calls return. Field names mirror the private
# schemas in app/tools and app/ingest, which is where they are validated.
LOCKOUT_INCIDENT_OVERRIDES: dict[str, dict] = {
    "_Verdict": {"document_type": "incident"},
    "_SeverityVerdict": {"tier": SeverityTier.CRITICAL},
    "_Verification": {"keep": []},
    # Two entities the pattern dictionary does not cover, plus one the model
    # invented -- the third must be dropped for not appearing in the document.
    "_EntityDiscovery": {
        "entities": [
            {"text": "disconnect", "entity_type": "EQUIPMENT"},
            {"text": "point of operation", "entity_type": "HAZARD"},
            {"text": "a hazard nobody wrote down", "entity_type": "HAZARD"},
        ]
    },
    "_GeneratedActions": {"actions": []},
    "_ParsedIncident": {
        "incident_date": "March 14, 2023",
        "location": "Rockford, Illinois",
        "industry": "manufacturing",
        "equipment_involved": ["hydraulic press", "conveyor"],
        "sequence_of_events": (
            "A maintenance technician entered the die area of a hydraulic press to clear a jam. "
            "The press had not been locked out and the machine was still running. "
            "The ram cycled and the technician was fatally injured."
        ),
        "immediate_causes": [
            "Energy isolation was not performed before entering the die area",
            "The technician did not verify a zero energy state",
        ],
        "root_causes": [
            "No machine-specific energy control procedure existed",
            "Production pressure discouraged shutdown for jam clearing",
        ],
        "injury_count": 0,
        "fatality_count": 1,
    },
}

PRIORITY_ALERT_TEXT = (
    "A maintenance technician was fatally injured clearing a jam on an unguarded, "
    "un-isolated hydraulic press. The same combination of a missing energy control "
    "procedure and an omitted verification step precedes repeat incidents on this "
    "class of equipment. Every press on the line shares the gap."
)
