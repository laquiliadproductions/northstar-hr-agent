"""Create human-readable citations from stored chunk metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

@dataclass(frozen=True)
class Citation:
    """Citation fields retained with a retrieved chunk."""

    title: str
    section: str
    source: str
    source_type: str
    snippet: str
    chunk_index: int
    page: int | None = None
    row: int | None = None

    @classmethod
    def from_metadata(
        cls,
        metadata: Mapping[str, Any],
    ) -> "Citation":
        """Validate metadata and create a citation object."""

        required = {
            "title",
            "section",
            "source",
            "source_type",
            "source_snippet",
            "chunk_index",
        }
        missing = required.difference(metadata)

        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(
                f"Citation metadata is missing: {missing_fields}"
            )

        return cls(
            title=str(metadata["title"]),
            section=str(metadata["section"]),
            source=str(metadata["source"]),
            source_type=str(metadata["source_type"]),
            snippet=str(metadata["source_snippet"]),
            chunk_index=int(metadata["chunk_index"]),
            page=(
                int(metadata["page"])
                if metadata.get("page") is not None
                else None
            ),
            row=(
                int(metadata["row"])
                if metadata.get("row") is not None
                else None
            ),
        )

    @property
    def source_id(self) -> str:
        """Return the source filename as a compact document ID."""

        return Path(self.source).name

    @property
    def locator(self) -> str:
        """Return the most useful location inside the source."""

        if self.page is not None:
            return f"page {self.page}"

        if self.row is not None:
            return f"row {self.row}"

        return self.section

    @property
    def label(self) -> str:
        """Return a compact title-and-location citation label."""

        parts = [self.title]

        if self.section and not self.section.lower().startswith("page "):
            parts.append(self.section)

        if self.page is not None:
            parts.append(f"page {self.page}")
        elif self.row is not None:
            parts.append(f"row {self.row}")

        return " — ".join(parts)

    def format(self, include_snippet: bool = True) -> str:
        """Render the citation for a user-facing response."""

        citation = f"[{self.label}]"

        if include_snippet and self.snippet:
            citation = f'{citation} "{self.snippet}"'

        return citation

def format_citation(
    metadata: Mapping[str, Any],
    include_snippet: bool = True,
) -> str:
    """Create one formatted citation directly from metadata."""

    return Citation.from_metadata(metadata).format(include_snippet)

def citations_from_query_result(
    result: Mapping[str, Any],
) -> list[Citation]:
    """Extract citations from a Chroma query result."""

    metadata_groups = result.get("metadatas") or []

    if not metadata_groups:
        return []

    return [
        Citation.from_metadata(metadata)
        for metadata in metadata_groups[0]
    ]

def format_query_citations(
    result: Mapping[str, Any],
    include_snippets: bool = True,
) -> list[str]:
    """Format every citation returned for one search query."""

    return [
        citation.format(include_snippet=include_snippets)
        for citation in citations_from_query_result(result)
    ]
