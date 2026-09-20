---
tags: [codegraph, layer]
---

# Retrieval

16 modules. Layer 2 of 6; imports may point down this list, never up.

| Module | In | Out | Symbols | Purpose |
|---|---|---|---|---|
| [[app.ingest]] | 0 | 0 | 0 | Document ingestion: load, clean, classify. |
| [[app.ingest.classifier]] | 1 | 1 | 3 | Decide what kind of document was uploaded. |
| [[app.ingest.loader]] | 1 | 1 | 3 | PDF text extraction: pdfplumber first, OCR only if the page layer is empty. |
| [[app.ingest.preprocessor]] | 1 | 0 | 3 | Turn raw page text into clean prose: drop running headers, fix line wrapping. |
| [[app.knowledge_graph]] | 0 | 0 | 0 | NetworkX knowledge graph over the incident corpus. |
| [[app.knowledge_graph.graph]] | 1 | 0 | 6 | NetworkX causal graph over the historical corpus. |
| [[app.knowledge_graph.serializer]] | 1 | 1 | 3 | Persist the knowledge graph as JSON on disk. |
| [[app.rag]] | 0 | 0 | 0 | Retrieval: chunking, embedding, indexing, hybrid search. |
| [[app.rag.bm25_index]] | 1 | 0 | 6 | Sparse keyword index. Built once by the ingest script, loaded read-only at runtime. |
| [[app.rag.chunker]] | 1 | 1 | 5 | Semantic chunking: split where the topic changes, not every N characters. |
| [[app.rag.compressor]] | 1 | 2 | 2 | Contextual compression: drop the sentences of a chunk that miss the query. |
| [[app.rag.embedder]] | 5 | 1 | 3 | bge-small-en-v1.5 embeddings. One model instance for the process. |
| [[app.rag.local_store]] | 1 | 2 | 8 | Brute-force vector search over a numpy array held in memory. |
| [[app.rag.qdrant_store]] | 1 | 2 | 9 | Qdrant backend, used when QDRANT_URL is set. |
| [[app.rag.retriever]] | 1 | 7 | 6 | Hybrid retrieval: BM25 + dense, merged with RRF, reranked by a cross-encoder. |
| [[app.rag.vector_store]] | 2 | 3 | 6 | Vector search façade over two real backends. |
