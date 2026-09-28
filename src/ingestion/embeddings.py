"""Generate free local embeddings for chunked documents."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from src.ingestion.loaders import ParsedDocument

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
DEFAULT_BATCH_SIZE = 32

_embedding_function: DefaultEmbeddingFunction | None = None

@dataclass
class EmbeddedDocument:
    """A text chunk, its citation metadata, and its vector."""

    id: str
    text: str
    metadata: dict[str, Any]
    embedding: list[float]

def get_embedding_function() -> DefaultEmbeddingFunction:
    """Create the local embedding model only when first needed."""

    global _embedding_function

    if _embedding_function is None:
        _embedding_function = DefaultEmbeddingFunction()

    return _embedding_function

def create_chunk_id(document: ParsedDocument) -> str:
    """Create a stable ID from the chunk's source metadata."""

    metadata = document.metadata
    identity = "|".join(
        [
            str(metadata.get("source", "")),
            str(metadata.get("page", "")),
            str(metadata.get("row", "")),
            str(metadata.get("section", "")),
            str(metadata.get("chunk_index", "")),
        ]
    )

    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"chunk-{digest[:24]}"

def to_float_list(vector: Any) -> list[float]:
    """Convert NumPy-like embedding output into plain Python floats."""

    values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
    return [float(value) for value in values]

def embed_chunks(
    documents: Iterable[ParsedDocument],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[EmbeddedDocument]:
    """Embed chunked documents in memory-efficient batches."""

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    document_list = list(documents)
    embedding_function = get_embedding_function()
    embedded_documents: list[EmbeddedDocument] = []

    for start in range(0, len(document_list), batch_size):
        batch = document_list[start : start + batch_size]
        vectors = embedding_function([document.text for document in batch])

        if len(vectors) != len(batch):
            raise RuntimeError("Embedding count does not match document count")

        for document, vector in zip(batch, vectors):
            embedding = to_float_list(vector)

            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                    f"received {len(embedding)}"
                )

            embedded_documents.append(
                EmbeddedDocument(
                    id=create_chunk_id(document),
                    text=document.text,
                    metadata=dict(document.metadata),
                    embedding=embedding,
                )
            )

    return embedded_documents

def embed_query(query: str) -> list[float]:
    """Embed one search query using the same local model."""

    if not query.strip():
        raise ValueError("query cannot be empty")

    vector = get_embedding_function()([query])[0]
    embedding = to_float_list(vector)

    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"received {len(embedding)}"
        )

    return embedding
