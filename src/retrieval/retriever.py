"""Retrieve ranked policy chunks from the vector store."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ingestion.vector_store import query_collection

@dataclass(frozen=True)
class RetrievalResult:
    """One policy chunk returned by semantic retrieval."""

    rank: int
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float

    @property
    def similarity(self) -> float:
        """Convert cosine distance into an intuitive similarity score."""

        return 1.0 - self.distance

def retrieve(
    query: str,
    top_k: int = 5,
    where: dict[str, Any] | None = None,
) -> list[RetrievalResult]:
    """Return the top-k policy chunks, optionally filtered by metadata."""

    raw_results = query_collection(
        query=query,
        n_results=top_k,
        where=where,
    )

    ids = raw_results["ids"][0]
    documents = raw_results["documents"][0]
    metadatas = raw_results["metadatas"][0]
    distances = raw_results["distances"][0]

    result_lengths = {
        len(ids),
        len(documents),
        len(metadatas),
        len(distances),
    }

    if len(result_lengths) != 1:
        raise RuntimeError("Chroma returned inconsistent result lengths")

    return [
        RetrievalResult(
            rank=rank,
            chunk_id=chunk_id,
            text=document,
            metadata=dict(metadata),
            distance=float(distance),
        )
        for rank, (chunk_id, document, metadata, distance) in enumerate(
            zip(ids, documents, metadatas, distances),
            start=1,
        )
    ]
