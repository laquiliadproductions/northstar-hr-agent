"""Tests for verified RAG citations."""

from __future__ import annotations
import unittest

from src.rag.citations import (
    build_citations,
    extract_source_numbers,
    normalize_source_markers,
)

from src.retrieval.retriever import RetrievalResult

class CitationTests(unittest.TestCase):
    """Verify source-marker parsing and metadata resolution."""

    def setUp(self) -> None:
        self.result = RetrievalResult(
            rank=2,
            chunk_id="chunk-pto",
            text=(
                "Employees receive 120, 160, or 200 hours of PTO "
                "depending on continuous service."
            ),

            metadata={
                "title": "Paid Time Off Policy",
                "source": "data/policies/pto.md",
                "section": "Annual accrual schedule",
            },

            distance=0.25,
        )

    def test_build_citations_resolves_verified_metadata(self) -> None:
        citations = build_citations(
            "PTO depends on service [Source 2].",
            [self.result],
        )

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].marker, "[Source 2]")
        self.assertEqual(citations[0].chunk_id, "chunk-pto")
        self.assertEqual(
            citations[0].section,
            "Annual accrual schedule",
        )

        self.assertIn("120, 160, or 200 hours", citations[0].snippet)

    def test_source_markers_are_normalized_for_display(self) -> None:
        answer = normalize_source_markers(
            "First\u202f[Source\u202f1]. "
            "Second【Source\u202f2, Source 3】."
        )

        self.assertEqual(
            answer,
            "First [Source 1]. Second[Source 2, Source 3].",
        )

    def test_unicode_space_in_marker_is_supported(self) -> None:
        numbers = extract_source_numbers(
            "Policy evidence [Source\u202f2]."
        )

        self.assertEqual(numbers, [2])

    def test_unicode_brackets_are_supported(self) -> None:
        numbers = extract_source_numbers(
            "Policy evidence 【Source\u202f2】."
        )

        self.assertEqual(numbers, [2])

    def test_unknown_source_number_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            build_citations(
                "Unsupported claim [Source 99].",
                [self.result],
            )

    def test_grouped_source_markers_are_supported(self) -> None:
        numbers = extract_source_numbers(
            "Approval is required [Source 3, Source 4]."
        )

        self.assertEqual(numbers, [3, 4])

if __name__ == "__main__":
    unittest.main()
