"""Decide what was uploaded and flag documents the pipeline cannot do much with."""

from __future__ import annotations

from ...config import settings
from ...ingest.classifier import classify
from ..state import SentinelState
from .base import NodeResult, node

_TYPE_MESSAGE = {
    "incident": "Incident report detected",
    "regulatory": "Regulatory document detected",
    "unknown": "Document type unclear",
}


@node("document_router", "Classifying document type...")
async def document_router(state: SentinelState) -> NodeResult:
    text = state["raw_text"]
    document_type = await classify(text)

    warnings = list(state.get("warnings", []))
    word_count = len(text.split())
    if word_count < settings.low_confidence_word_count:
        warnings.append(f"Document is only {word_count} words. Findings are low confidence.")
    if document_type != "incident":
        warnings.append(
            f"Document classified as '{document_type}'. SENTINEL analyses incident reports; "
            "results may be thin."
        )

    return NodeResult(
        updates={"document_type": document_type, "warnings": warnings},
        message=f"{_TYPE_MESSAGE[document_type]} ({word_count} words)",
        data={"document_type": document_type, "word_count": word_count},
    )
