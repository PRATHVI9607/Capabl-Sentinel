"""bge-small-en-v1.5 embeddings. One model instance for the process.

Served through `fastembed` (ONNX Runtime) rather than `sentence-transformers`.
It is the same model and the same vectors, without a PyTorch dependency:
roughly 150MB installed against 2.5GB, which is the difference between a build
that fits a free-tier instance and one that does not.

fastembed returns L2-normalised vectors and applies bge's asymmetric query
prefix itself, so callers get cosine similarity from a plain dot product.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

import numpy as np

from ..config import settings

# bge-small-en-v1.5. Hard-coded so a vector store can be provisioned before the
# model has been downloaded.
EMBEDDING_DIM = 384
EMBED_BATCH_SIZE = 64


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(
        model_name=settings.embedding_model,
        cache_dir=str(settings.data_dir / "fastembed"),
    )


def embed_documents(texts: Sequence[str]) -> np.ndarray:
    """Document embeddings, shape (len(texts), EMBEDDING_DIM)."""
    if not texts:
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)
    vectors = list(_model().embed(list(texts), batch_size=EMBED_BATCH_SIZE))
    return np.asarray(vectors, dtype=np.float32)


def embed_query(text: str) -> np.ndarray:
    """Query embedding, shape (EMBEDDING_DIM,). Carries bge's query prefix."""
    return np.asarray(next(iter(_model().query_embed(text))), dtype=np.float32)
