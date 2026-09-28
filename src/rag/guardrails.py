"""Deterministic guardrails for grounded policy answers."""

from __future__ import annotations
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from src.rag.citations import Citation
from src.retrieval.retriever import RetrievalResult

MIN_RELEVANCE_SIMILARITY = 0.25

OUT_OF_CORPUS_RESPONSE = (
    "I can answer questions about Northstar Analytics policies using the "
    "available policy corpus. I could not find sufficiently relevant policy "
    "content for this question. Try asking about topics such as paid time "
    "off, leave, benefits enrollment, travel, expenses, workplace conduct, "
    "remote work, or performance."
)

class AnswerStatus(str, Enum):
    """Grounding status assigned to a RAG response."""

    GROUNDED = "grounded"
    OUT_OF_CORPUS = "out_of_corpus"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

@dataclass(frozen=True)
class RetrievalGate:
    """Decision made before calling the language model."""

    allowed: bool
    best_similarity: float
    response: str | None = None

def check_retrieval(
    results: Sequence[RetrievalResult],
    minimum_similarity: float = MIN_RELEVANCE_SIMILARITY,
) -> RetrievalGate:
    """Reject retrieval results that are clearly unrelated."""

    if not 0.0 <= minimum_similarity <= 1.0:
        raise ValueError(
            "minimum_similarity must be between zero and one"
        )

    if not results:
        return RetrievalGate(
            allowed=False,
            best_similarity=0.0,
            response=OUT_OF_CORPUS_RESPONSE,
        )

    best_similarity = max(result.similarity for result in results)

    if best_similarity < minimum_similarity:
        return RetrievalGate(
            allowed=False,
            best_similarity=best_similarity,
            response=OUT_OF_CORPUS_RESPONSE,
        )

    return RetrievalGate(
        allowed=True,
        best_similarity=best_similarity,
    )

def classify_answer(
    citations: Sequence[Citation],
) -> AnswerStatus:
    """Classify a generated response by its verified citation support."""

    if citations:
        return AnswerStatus.GROUNDED

    return AnswerStatus.INSUFFICIENT_EVIDENCE
