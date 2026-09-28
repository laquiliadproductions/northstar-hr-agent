"""Tests for structured policy retrieval."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.retrieval.retriever import retrieve

class RetrieverTests(unittest.TestCase):
    """Verify conversion of raw Chroma results."""

    @patch("src.retrieval.retriever.query_collection")
    def test_retrieve_returns_ranked_results_and_forwards_filter(
        self,
        mock_query_collection,
    ) -> None:
        policy_filter = {"title": "Paid Time Off Policy"}
        mock_query_collection.return_value = {
            "ids": [["chunk-a", "chunk-b"]],
            "documents": [["Accrual schedule", "Eligibility rules"]],
            "metadatas": [[
                {"title": "Paid Time Off Policy", "section": "Accrual"},
                {"title": "Paid Time Off Policy", "section": "Scope"},
            ]],
            "distances": [[0.25, 0.40]],
        }

        results = retrieve(
            "How much PTO do employees receive?",
            top_k=2,
            where=policy_filter,
        )

        mock_query_collection.assert_called_once_with(
            query="How much PTO do employees receive?",
            n_results=2,
            where=policy_filter,
        )

        self.assertEqual([result.rank for result in results], [1, 2])
        self.assertEqual(results[0].chunk_id, "chunk-a")
        self.assertEqual(results[0].text, "Accrual schedule")
        self.assertEqual(results[0].metadata["section"], "Accrual")
        self.assertAlmostEqual(results[0].similarity, 0.75)

if __name__ == "__main__":
    unittest.main()
