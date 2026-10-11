"""Loading and validation for Section 9 evaluation cases."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


EVALUATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "evaluation"
    / "northstar_section9_evaluation_set.json"
)

EvaluationCase = dict[str, Any]


@lru_cache(maxsize=1)
def load_evaluation_cases() -> dict[str, EvaluationCase]:
    """Load the evaluation set and index its cases by ID."""

    if not EVALUATION_PATH.is_file():
        raise FileNotFoundError(
            f"Evaluation set not found: {EVALUATION_PATH}"
        )

    data = json.loads(
        EVALUATION_PATH.read_text(encoding="utf-8")
    )
    cases = data.get("cases")

    if not isinstance(cases, list):
        raise ValueError(
            "The evaluation set must contain a cases list."
        )

    indexed_cases: dict[str, EvaluationCase] = {}

    for case in cases:
        if not isinstance(case, dict):
            raise ValueError(
                "Each evaluation case must be an object."
            )

        case_id = case.get("id")

        if not isinstance(case_id, str) or not case_id:
            raise ValueError(
                "Each evaluation case must have a non-empty ID."
            )

        if case_id in indexed_cases:
            raise ValueError(
                f"Duplicate evaluation case ID: {case_id}"
            )

        indexed_cases[case_id] = case

    return indexed_cases


def get_evaluation_case(
    case_id: str,
) -> EvaluationCase:
    """Return one evaluation case or raise a clear error."""

    cases = load_evaluation_cases()

    try:
        return cases[case_id]
    except KeyError as error:
        raise KeyError(
            f"Unknown evaluation case ID: {case_id}"
        ) from error
