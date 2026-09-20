"""One-time: load the historical incident corpus into Qdrant, BM25 and the graph.

    python scripts/ingest_corpus.py

Reads every PDF/TXT in backend/data/incidents/, chunks it semantically, indexes
it, and writes the corpus manifest that the risk score's frequency component
reads. Re-running is safe: chunk ids are content-derived, so upserts replace.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _ingest_common import (
    METADATA_WINDOW,
    DocumentLoadError,
    chunk_id_for,
    detect_date,
    detect_industry,
    index_chunks,
    read_document,
    semantic_chunks,
    source_files,
)

from app.config import settings
from app.knowledge_graph import graph as kg
from app.knowledge_graph import serializer
from app.models import EntityType
from app.tools.parsing import spacy_entities
from app.tools.patterns import detect_hazard_type
from app.tools.scoring import classify_severity_by_rules


def document_metadata(path: Path, text: str) -> dict[str, str]:
    """Classify a corpus document from its full text.

    Industry, hazard family and severity are keyword scans, so reading the whole
    document costs almost nothing and is far more accurate. A formal
    investigation report opens with a cover page, contents and legal notice: the
    first 8,000 characters contain none of the incident. Classifying from that
    window labelled a chemical release as `general` and a chemical fire as
    `construction` -- wrong metadata, which then drives the retrieval filter and
    selects the precursor taxonomy.

    The date still comes from the front matter, where the incident date is
    stated, rather than from the first date mentioned anywhere in the body.
    """
    severity = classify_severity_by_rules(text)
    return {
        "title": path.stem.replace("_", " "),
        "source_document": path.name,
        "industry": detect_industry(text),
        "severity": severity.value if severity else "UNKNOWN",
        "hazard_type": detect_hazard_type(text),
        "incident_date": detect_date(text[:METADATA_WINDOW]),
    }


def add_to_graph(graph, document_name: str, text: str, metadata: dict[str, str]) -> None:
    entities = spacy_entities(text)
    by_type = {
        entity_type: tuple(e.text for e in entities if e.entity_type is entity_type)
        for entity_type in EntityType
    }
    kg.add_incident(
        graph,
        document_name,
        title=metadata["title"],
        industry=metadata["industry"],
        severity=metadata["severity"],
        equipment=by_type[EntityType.EQUIPMENT],
        hazards=by_type[EntityType.HAZARD],
        causes=by_type[EntityType.UNSAFE_ACT] + by_type[EntityType.CONDITION],
    )
    # An unsafe condition reported alongside a hazard is treated as preceding it.
    for hazard in by_type[EntityType.HAZARD]:
        for condition in by_type[EntityType.CONDITION]:
            kg.link_precursor(graph, kg.node_key("condition", condition), kg.node_key("hazard", hazard))


def main() -> int:
    directory = settings.data_dir / "incidents"
    documents = source_files(directory)
    if not documents:
        print(f"No documents found in {directory}. See data/incidents/README.md for sources.")
        return 1

    graph = kg.new_graph()
    chunk_ids: list[str] = []
    payloads: list[dict] = []

    for path in documents:
        try:
            text = read_document(path)
        except DocumentLoadError as exc:
            print(f"! skipping {path.name}: {exc}")
            continue

        metadata = document_metadata(path, text)
        chunks = semantic_chunks(text, metadata=metadata)
        industry = metadata["industry"]
        hazard = metadata["hazard_type"]
        print(f"- {path.name}: {len(chunks)} chunks ({industry}, {hazard})")

        for index, chunk in enumerate(chunks):
            chunk_id = chunk_id_for(path.name, index, chunk.text)
            chunk_ids.append(chunk_id)
            payloads.append(
                {**metadata, "chunk_id": chunk_id, "text": chunk.text, "section": chunk.section}
            )
        add_to_graph(graph, path.name, text, metadata)

    index_chunks(settings.incidents_collection, chunk_ids, payloads)
    serializer.save(graph)
    print(f"Knowledge graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    manifest = {"document_count": len(documents), "chunk_count": len(chunk_ids)}
    (settings.data_dir / "corpus_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
