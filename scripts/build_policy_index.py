"""Rebuild the persistent Northstar policy vector index."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.chunkers import chunk_documents
from src.ingestion.embeddings import embed_chunks
from src.ingestion.loaders import load_directory
from src.ingestion.vector_store import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_DB_PATH,
    collection_count,
    reset_collection,
    upsert_embeddings,
)

POLICY_DIRECTORY = Path("data/policies")

def main() -> None:
    """Run the complete policy indexing pipeline."""

    os.chdir(PROJECT_ROOT)
    started = time.perf_counter()

    print("1. Loading policy documents...", flush=True)
    parsed_documents = load_directory(POLICY_DIRECTORY)
    source_count = len(
        {
            document.metadata["source"]
            for document in parsed_documents
        }
    )
    print(
        f"   Loaded {source_count} files "
        f"as {len(parsed_documents)} parsed units."
    )

    print("2. Chunking policy documents...", flush=True)
    chunks = chunk_documents(parsed_documents)
    print(f"   Created {len(chunks)} chunks.")

    print("3. Generating local embeddings...", flush=True)
    embedded_documents = embed_chunks(chunks, batch_size=32)
    print(
        f"   Generated {len(embedded_documents)} "
        f"384-dimensional vectors."
    )

    print("4. Rebuilding the Chroma collection...", flush=True)
    reset_collection(
        database_path=DEFAULT_DB_PATH,
        collection_name=DEFAULT_COLLECTION_NAME,
    )
    stored_count = upsert_embeddings(
        embedded_documents,
        database_path=DEFAULT_DB_PATH,
        collection_name=DEFAULT_COLLECTION_NAME,
    )
    final_count = collection_count(
        database_path=DEFAULT_DB_PATH,
        collection_name=DEFAULT_COLLECTION_NAME,
    )

    if stored_count != final_count:
        raise RuntimeError(
            f"Stored {stored_count} chunks, "
            f"but Chroma contains {final_count}"
        )

    elapsed = time.perf_counter() - started

    print(f"   Stored {final_count} chunks.")
    print(
        f"Index complete in {elapsed:.2f} seconds. "
        f"Database: {DEFAULT_DB_PATH}"
    )

if __name__ == "__main__":

    main()
