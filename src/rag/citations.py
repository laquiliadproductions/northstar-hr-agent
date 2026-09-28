"""Create verified citations from retrieved policy chunks."""

from __future__ import annotations
from collections.abc import Sequence
from dataclasses import dataclass

import re

from src.retrieval.retriever import RetrievalResult

SOURCE_GROUP_PATTERN = re.compile(r"\[([^\]]+)\]")
SOURCE_NUMBER_PATTERN = re.compile(
    r"\bSource\s+(\d+)\b",
    flags=re.IGNORECASE,
)

DEFAULT_SNIPPET_LENGTH = 500

@dataclass(frozen=True)
class Citation:
    """Verified source metadata associated with an answer marker."""

    source_number: int
    chunk_id: str
    title: str
    document: str
    section: str
    snippet: str
    page: int | None = None
    row: int | None = None

    @property

    def marker(self) -> str:
        """Return the marker used in the generated answer."""

        return f"[Source {self.source_number}]"

def create_snippet(
    result: RetrievalResult,
    max_length: int = DEFAULT_SNIPPET_LENGTH,
) -> str:

    """Return a compact supporting excerpt from a retrieved chunk."""

    if max_length <= 0:
        raise ValueError("max_length must be greater than zero")

    source_text = result.text
    normalized = re.sub(r"\s+", " ", source_text).strip()

    if len(normalized) <= max_length:
        return normalized

    return normalized[: max_length - 3].rstrip() + "..."

def extract_source_numbers(answer: str) -> list[int]:
    """Return unique cited source numbers in their first-used order."""

    numbers: list[int] = []

    for group_match in SOURCE_GROUP_PATTERN.finditer(answer):
        group_text = group_match.group(1)

        for number_match in SOURCE_NUMBER_PATTERN.finditer(group_text):
            number = int(number_match.group(1))

            if number not in numbers:
                numbers.append(number)

    return numbers

def build_citations(
    answer: str,
    results: Sequence[RetrievalResult],
) -> list[Citation]:

    """Resolve answer markers against actual retrieved results."""
    result_by_rank = {result.rank: result for result in results}
    citations: list[Citation] = []

    for source_number in extract_source_numbers(answer):
        if source_number not in result_by_rank:
            raise RuntimeError(
                f"Answer cited unknown source number {source_number}"
            )

        result = result_by_rank[source_number]
        metadata = result.metadata

        citations.append(
            Citation(
                source_number=source_number,
                chunk_id=result.chunk_id,
                title=str(metadata.get("title", "Unknown title")),
                document=str(metadata.get("source", "Unknown source")),
                section=str(metadata.get("section", "Unknown section")),
                snippet=create_snippet(result),
                page=(
                    int(metadata["page"])
                    if "page" in metadata
                    else None
                ),
                row=(
                    int(metadata["row"])
                    if "row" in metadata
                    else None
                ),
            )
        )

    return citations
