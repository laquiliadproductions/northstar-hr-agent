"""Persist and query embedded policy chunks with Chroma."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import chromadb

from src.ingestion.embeddings import (
    EMBEDDING_MODEL,
    EmbeddedDocument,
    embed_query,
)

DEFAULT_DB_PATH = Path("chroma_db")
DEFAULT_COLLECTION_NAME = "northstar_policies"
DEFAULT_BATCH_SIZE = 100

def get_client(
    database_path: str | Path = DEFAULT_DB_PATH,
) -> Any:
    """Return a persistent local Chroma client."""

    path = Path(database_path)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))

def get_collection(
    database_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Any:
    """Open or create the cosine-similarity policy collection."""

    client = get_client(database_path)

    return client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "Northstar Analytics policy chunks",
            "embedding_model": EMBEDDING_MODEL,
            "hnsw:space": "cosine",
        },
    )

def prepare_metadata(
    metadata: dict[str, Any],
) -> dict[str, str | int | float | bool]:
    """Convert metadata into Chroma-supported scalar values."""

    prepared: dict[str, str | int | float | bool] = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            prepared[key] = value
        else:
            prepared[key] = str(value)

    return prepared

def upsert_embeddings(
    documents: Iterable[EmbeddedDocument],
    database_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """Insert or update embedded documents in persistent Chroma."""

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    document_list = list(documents)
    collection = get_collection(database_path, collection_name)

    for start in range(0, len(document_list), batch_size):
        batch = document_list[start : start + batch_size]

        collection.upsert(
            ids=[document.id for document in batch],
            documents=[document.text for document in batch],
            metadatas=[
                prepare_metadata(document.metadata)
                for document in batch
            ],
            embeddings=[
                document.embedding
                for document in batch
            ],
        )

    return len(document_list)

def query_collection(
    query: str,
    n_results: int = 5,
    where: dict[str, Any] | None = None,
    database_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> dict[str, Any]:
    """Run semantic similarity search against the policy collection."""

    if n_results <= 0:
        raise ValueError("n_results must be greater than zero")

    collection = get_collection(database_path, collection_name)
    collection_size = collection.count()

    if collection_size == 0:
        raise RuntimeError("The policy collection is empty")

    result_count = min(n_results, collection_size)

    query_arguments: dict[str, Any] = {
        "query_embeddings": [embed_query(query)],
        "n_results": result_count,
        "include": ["documents", "metadatas", "distances"],
    }

    if where:
        query_arguments["where"] = where

    return collection.query(**query_arguments)
def collection_count(
    database_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> int:
    """Return the number of stored chunks."""

    return get_collection(database_path, collection_name).count()

def reset_collection(
    database_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Any:
    """Delete and recreate one collection for a clean rebuild."""

    client = get_client(database_path)
    existing_names = {
        collection.name
        for collection in client.list_collections()
    }

    if collection_name in existing_names:
        client.delete_collection(collection_name)

    return client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "Northstar Analytics policy chunks",
            "embedding_model": EMBEDDING_MODEL,
            "hnsw:space": "cosine",
        },
    )
