"""Tests for deterministic RAG guardrails."""

from __future__ import annotations
import unittest
from src.rag.citations import Citation
from src.rag.guardrails import (
    AnswerStatus,
    check_retrieval,
    classify_answer,
)

from src.retrieval.retriever import RetrievalResult

def make_result(similarity: float) -> RetrievalResult:
    """Create a retrieval result with a chosen similarity."""

    return RetrievalResult(
        rank=1,
        chunk_id="chunk-test",
        text="Policy evidence",
        metadata={
            "title": "Test Policy",
            "source": "data/policies/test.md",
            "section": "Test Section",
        },
        distance=1.0 - similarity,
    )

class GuardrailTests(unittest.TestCase):
    """Verify relevance gating and answer classification."""

    def test_low_similarity_is_rejected(self) -> None:
        gate = check_retrieval([make_result(0.14)])

        self.assertFalse(gate.allowed)
        self.assertAlmostEqual(gate.best_similarity, 0.14)
        self.assertIsNotNone(gate.response)

    def test_sufficient_similarity_is_allowed(self) -> None:
        gate = check_retrieval([make_result(0.63)])

        self.assertTrue(gate.allowed)
        self.assertAlmostEqual(gate.best_similarity, 0.63)
        self.assertIsNone(gate.response)

    def test_empty_results_are_rejected(self) -> None:
        gate = check_retrieval([])

        self.assertFalse(gate.allowed)
        self.assertEqual(gate.best_similarity, 0.0)

    def test_verified_citation_is_grounded(self) -> None:
        citation = Citation(
            source_number=1,
            chunk_id="chunk-test",
            title="Test Policy",
            document="data/policies/test.md",
            section="Test Section",
            snippet="Policy evidence",
        )

        self.assertEqual(
            classify_answer([citation]),
            AnswerStatus.GROUNDED,
        )

    def test_no_citations_is_insufficient_evidence(self) -> None:
        self.assertEqual(
            classify_answer([]),
            AnswerStatus.INSUFFICIENT_EVIDENCE,
        )

if __name__ == "__main__":
    unittest.main()
