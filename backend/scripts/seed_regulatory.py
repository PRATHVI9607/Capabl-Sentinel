"""One-time: load regulatory standards into the regulatory Qdrant collection.

    python scripts/seed_regulatory.py

Reads every PDF/TXT in backend/data/regulatory/. The file name becomes the
citation shown in the UI, so name each file after the standard it contains,
e.g. `OSHA 29 CFR 1910.147.txt`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _ingest_common import (
    METADATA_WINDOW,
    DocumentLoadError,
    chunk_id_for,
    index_chunks,
    read_document,
    semantic_chunks,
    source_files,
)

from app.config import settings
from app.tools.patterns import detect_hazard_type
from app.tools.retrieval import clause_family


def main() -> int:
    directory = settings.data_dir / "regulatory"
    documents = source_files(directory)
    if not documents:
        print(f"No documents found in {directory}. See data/regulatory/README.md for sources.")
        return 1

    chunk_ids: list[str] = []
    payloads: list[dict] = []

    for path in documents:
        try:
            text = read_document(path)
        except DocumentLoadError as exc:
            print(f"! skipping {path.name}: {exc}")
            continue

        regulation_name = path.stem.replace("_", " ")
        metadata = {
            "regulation_name": regulation_name,
            "source_document": path.name,
            "clause_family": clause_family(regulation_name),
            "hazard_type": detect_hazard_type(text[:METADATA_WINDOW]),
        }
        chunks = semantic_chunks(text, metadata=metadata)
        family = metadata["clause_family"]
        print(f"- {regulation_name}: {len(chunks)} chunks ({family})")

        for index, chunk in enumerate(chunks):
            chunk_id = chunk_id_for(path.name, index, chunk.text)
            chunk_ids.append(chunk_id)
            payloads.append(
                {**metadata, "chunk_id": chunk_id, "text": chunk.text, "section": chunk.section}
            )

    index_chunks(settings.regulatory_collection, chunk_ids, payloads)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
