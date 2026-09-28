"""Run retrieval and grounded answer generation."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from langchain_openai import ChatOpenAI
from config import RETRIEVAL_TOP_K
from settings import get_settings
from src.rag.citations import Citation, build_citations

from src.rag.guardrails import (
    AnswerStatus,
    OUT_OF_CORPUS_RESPONSE,
    check_retrieval,
    classify_answer,
)

from src.rag.prompts import build_grounded_messages
from src.rag.prompts import build_grounded_messages
from src.retrieval.retriever import RetrievalResult, retrieve

@dataclass(frozen=True)
class RAGAnswer:
    """A generated answer and the policy evidence used to create it."""

    question: str
    answer: str
    sources: tuple[RetrievalResult, ...]
    citations: tuple[Citation, ...]
    status: AnswerStatus
    best_similarity: float

def create_chat_model() -> ChatOpenAI:
    """Create the configured OpenAI-compatible chat model."""

    settings = get_settings()

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=60,
        max_retries=2,
    )

def answer_question(
    question: str,
    top_k: int = RETRIEVAL_TOP_K,
    where: dict[str, Any] | None = None,
) -> RAGAnswer:
    """Retrieve policy evidence and generate a grounded answer."""

    results = retrieve(
        query=question,
        top_k=top_k,
        where=where,
    )

    retrieval_gate = check_retrieval(results)

    if not retrieval_gate.allowed:
        return RAGAnswer(
            question=question,
            answer=retrieval_gate.response or OUT_OF_CORPUS_RESPONSE,
            sources=tuple(results),
            citations=(),
            status=AnswerStatus.OUT_OF_CORPUS,
            best_similarity=retrieval_gate.best_similarity,
        )

    messages = build_grounded_messages(question, results)
    response = create_chat_model().invoke(messages)

    if not isinstance(response.content, str):
        raise RuntimeError("The model returned non-text content")

    answer = response.content.strip()
    citations = build_citations(answer, results)

    return RAGAnswer(
        question=question,
        answer=answer,
        sources=tuple(results),
        citations=tuple(citations),
        status=classify_answer(citations),
        best_similarity=retrieval_gate.best_similarity,
    )
