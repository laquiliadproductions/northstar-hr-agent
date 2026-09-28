"""Create citation-friendly chunks from parsed documents."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

import tiktoken

from src.ingestion.loaders import ParsedDocument

DEFAULT_MAX_TOKENS = 200
DEFAULT_OVERLAP_TOKENS = 30
TOKEN_ENCODING = tiktoken.get_encoding("cl100k_base")

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

def count_tokens(text: str) -> int:
    """Return the approximate model-token count for text."""

    return len(TOKEN_ENCODING.encode(text))

def token_windows(
    text: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[str]:

    """Split text into overlapping token windows."""
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than zero")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens cannot be negative")
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be smaller than max_tokens")

    tokens = TOKEN_ENCODING.encode(text)

    if not tokens:
        return []

    if len(tokens) <= max_tokens:
        return [text.strip()]

    windows: list[str] = []
    step = max_tokens - overlap_tokens

    for start in range(0, len(tokens), step):
        window_tokens = tokens[start : start + max_tokens]
        window_text = TOKEN_ENCODING.decode(window_tokens).strip()

        if window_text:
            windows.append(window_text)

        if start + max_tokens >= len(tokens):
            break

    return windows

def markdown_sections(text: str) -> list[tuple[str, str, str]]:
    """Return section name, heading line, and body for Markdown text."""

    sections: list[tuple[str, str, str]] = []
    current_name = "Document Overview"
    current_heading = ""
    current_body: list[str] = []

    for line in text.splitlines():
        match = HEADING_PATTERN.match(line)

        if match:
            body = "\n".join(current_body).strip()

            if body:
                sections.append(
                    (current_name, current_heading, body)
                )

            current_name = match.group(2).strip()
            current_heading = line.strip()
            current_body = []
        else:
            current_body.append(line)

    body = "\n".join(current_body).strip()

    if body:
        sections.append((current_name, current_heading, body))

    if not sections and text.strip():
        sections.append(("Document Overview", "", text.strip()))

    return sections

def chunk_markdown(
    document: ParsedDocument,
    max_tokens: int,
    overlap_tokens: int,
) -> list[ParsedDocument]:

    """Chunk Markdown by heading, then split oversized sections."""
    chunks: list[ParsedDocument] = []

    for section_name, heading, body in markdown_sections(document.text):
        prefix = f"{heading}\n\n" if heading else ""
        prefix_tokens = count_tokens(prefix)
        body_limit = max(1, max_tokens - prefix_tokens - 4)
        body_overlap = min(overlap_tokens, body_limit - 1)

        for part in token_windows(body, body_limit, body_overlap):
            text = f"{prefix}{part}".strip()
            metadata = dict(document.metadata)
            metadata["section"] = section_name
            metadata["token_count"] = count_tokens(text)
            metadata["source_snippet"] = re.sub(
                r"\s+",
                " ",
                text,
            )[:240]

            chunks.append(
                ParsedDocument(text=text, metadata=metadata)
            )

    return chunks

def chunk_document(
    document: ParsedDocument,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[ParsedDocument]:
    """Chunk one parsed document according to its source type."""

    source_type = document.metadata.get("source_type")

    if source_type == "markdown":
        return chunk_markdown(
            document,
            max_tokens,
            overlap_tokens,
        )

    if source_type == "csv":
        metadata = dict(document.metadata)
        metadata["section"] = f"Row {metadata.get('row', 'unknown')}"
        metadata["token_count"] = count_tokens(document.text)
        metadata["source_snippet"] = re.sub(
            r"\s+",
            " ",
            document.text,
        )[:240]

        return [
            ParsedDocument(
                text=document.text,
                metadata=metadata,
            )
        ]

    if source_type == "pdf":
        section = f"Page {document.metadata.get('page', 'unknown')}"
        chunks: list[ParsedDocument] = []

        for part in token_windows(
            document.text,
            max_tokens - 4,
            overlap_tokens,
        ):
            metadata = dict(document.metadata)
            metadata["section"] = section
            metadata["token_count"] = count_tokens(part)
            metadata["source_snippet"] = re.sub(
                r"\s+",
                " ",
                part,
            )[:240]

            chunks.append(
                ParsedDocument(text=part, metadata=metadata)
            )

        return chunks

    raise ValueError(f"Unsupported source type: {source_type}")

def chunk_documents(
    documents: Iterable[ParsedDocument],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[ParsedDocument]:
    """Chunk documents and assign an index within each source file."""

    chunks: list[ParsedDocument] = []
    source_indexes: defaultdict[str, int] = defaultdict(int)

    for document in documents:
        for chunk in chunk_document(
            document,
            max_tokens,
            overlap_tokens,
        ):
            source = str(chunk.metadata["source"])
            chunk.metadata["chunk_index"] = source_indexes[source]
            source_indexes[source] += 1
            chunks.append(chunk)

    return chunks
