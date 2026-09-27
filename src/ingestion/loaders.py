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

def markdown_title(text: str, fallback: str) -> str:
    """Use the first level-one Markdown heading as the title."""

    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback

def load_markdown(path: Path) -> list[ParsedDocument]:
    """Load one Markdown file."""

    text = clean_text(path.read_text(encoding="utf-8"))

    if not text:
        return []

    return [
        ParsedDocument(
            text=text,

            metadata={
                "title": markdown_title(text, path.stem),
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
                    "title": path.stem,
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

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=2):
            fields = [
                f"{column}: {clean_text(value)}"

                for column, value in row.items()
                if column and value and clean_text(value)
            ]
            text = "\n".join(fields)

            if not text:
                continue

            documents.append(
                ParsedDocument(
                    text=text,
                    metadata={
                        "title": path.stem,
                        "source": str(path),
                        "source_type": "csv",
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
