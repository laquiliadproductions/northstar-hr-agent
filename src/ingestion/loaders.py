"""Load and clean Markdown, PDF, and CSV source files."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

@dataclass

class ParsedDocument:
    """Clean text and citation metadata from one source unit."""

    text: str
    metadata: dict[str, Any]

def clean_text(text: str) -> str:
    """Normalize text while preserving headings and paragraph boundaries."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def source_title(path: Path) -> str:
    """Convert a numbered source filename into a readable title."""

    title = re.sub(r"^\d+\.", "", path.stem)
    title = re.sub(r"[_-]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()

def markdown_title(text: str, fallback: str) -> str:
    """Use a non-numbered H1 heading or a cleaned filename."""

    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)

    if not match:
        return fallback

    title = match.group(1).strip()

    if re.match(r"^\d+(?:\.\d+)*\s+", title):
        return fallback

    return title

def load_markdown(path: Path) -> list[ParsedDocument]:
    """Load one Markdown file."""

    text = clean_text(path.read_text(encoding="utf-8"))

    if not text:
        return []

    return [
        ParsedDocument(
            text=text,

            metadata={
                "title": markdown_title(text, source_title(path)),
                "source": str(path),
                "source_type": "markdown",
            },
        )
    ]

def load_pdf(path: Path) -> list[ParsedDocument]:
    """Load a PDF as one document per nonempty page."""

    reader = PdfReader(path)
    documents: list[ParsedDocument] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")

        if not text:
            continue

        documents.append(
            ParsedDocument(
                text=text,
                metadata={
                    "title": source_title(path),
                    "source": str(path),
                    "source_type": "pdf",
                    "page": page_number,
                },
            )
        )

    return documents

def load_csv(path: Path) -> list[ParsedDocument]:
    """Load synthetic structured data as one document per CSV row."""

    documents: list[ParsedDocument] = []

    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                rows = list(csv.reader(file))
            break
        except UnicodeDecodeError:
            continue

    else:
        raise UnicodeError(f"Could not decode CSV file: {path}")

    if not rows:
        return documents

    # Spreadsheet exports may contain report titles and summaries above
    # the real header. The first highly populated row is usually the header.

    candidate_rows = rows[:20]
    header_index = max(

        range(len(candidate_rows)),
        key=lambda index: sum(
            bool(cell.strip()) for cell in candidate_rows[index]
        ),
    )

    headers = [clean_text(cell) for cell in rows[header_index]]
    populated_headers = [header for header in headers if header]

    if len(populated_headers) < 2:
        raise ValueError(f"Could not identify a CSV header row in {path}")

    for row_number, values in enumerate(
        rows[header_index + 1 :],
        start=header_index + 2,
    ):
        row = {
            header: value
            for header, value in zip(headers, values)
            if header
        }

        fields = [
            f"{column}: {clean_text(value)}"
            for column, value in row.items()
            if value and clean_text(value)
        ]
        text = "\n".join(fields)

        if not text:
            continue

        documents.append(
            ParsedDocument(
                text=text,
                metadata={
                    "title": source_title(path),
                    "source": str(path),
                    "source_type": "csv",
                    "header_row": header_index + 1,
                    "row": row_number,
                },
            )
        )
    return documents

def load_document(file_path: str | Path) -> list[ParsedDocument]:
    """Select the appropriate loader based on the file extension."""

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in {".md", ".markdown"}:
        return load_markdown(path)

    if suffix == ".pdf":
        return load_pdf(path)

    if suffix == ".csv":
        return load_csv(path)

    raise ValueError(f"Unsupported file type: {suffix}")





def load_directory(
    directory_path: str | Path,
    extensions: set[str] | None = None,
) -> list[ParsedDocument]:
    """Load all supported files directly inside a directory."""

    directory = Path(directory_path)

    if not directory.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory}")

    supported = extensions or {".md", ".markdown", ".pdf", ".csv"}
    documents: list[ParsedDocument] = []

    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in supported:
            documents.extend(load_document(path))

    return documents
