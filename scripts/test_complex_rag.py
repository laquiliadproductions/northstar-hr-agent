"""Run the required complex multi-document RAG evaluation."""

from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.pipeline import answer_question

QUESTION = (
    "A U.S.-based employee wants to work remotely from another country "
    "for ten business days and take three PTO days during that period. "
    "What advance approvals, timing and duration limits, PTO eligibility, "
    "and PTO recording rules apply?"
)

def main() -> None:
    """Run and display the complex evaluation case."""

    result = answer_question(QUESTION, top_k=8)

    print(f"Status: {result.status.value}")
    print(f"Best similarity: {result.best_similarity:.4f}")
    print("\nANSWER\n")
    print(result.answer)
    print("\nVERIFIED CITATIONS")

    for citation in result.citations:
        print(
            f"{citation.marker} {citation.title} — "
            f"{citation.section}"
        )

    unique_documents = {
        citation.document
        for citation in result.citations
    }

    print(f"\nUnique cited documents: {len(unique_documents)}")

if __name__ == "__main__":
    main()
