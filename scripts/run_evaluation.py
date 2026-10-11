"""Run the Northstar Section 9 evaluation suite."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.web.app import app


EVALUATION_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "northstar_section9_evaluation_set.json"
)

BINARY_METRICS = {
    "groundedness",
    "citation_accuracy",
    "tool_selection_accuracy",
    "workflow_completion",
    "clarification_or_escalation_accuracy",
    "action_safety",
}

METRIC_NAMES = (
    "groundedness",
    "citation_accuracy",
    "gold_answer_match",
    "tool_selection_accuracy",
    "workflow_completion",
    "clarification_or_escalation_accuracy",
    "action_safety",
)


def percentile(
    values: list[float],
    percentile_value: float,
) -> float | None:
    """Calculate an interpolated percentile without extra packages."""

    if not values:
        return None

    ordered = sorted(values)

    if len(ordered) == 1:
        return round(ordered[0], 2)

    position = (len(ordered) - 1) * percentile_value
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index

    result = (
        ordered[lower_index]
        + (
            ordered[upper_index]
            - ordered[lower_index]
        )
        * fraction
    )

    return round(result, 2)


def case_passed(
    case: dict[str, Any],
    metrics: dict[str, Any],
) -> bool:
    """Apply deterministic per-case pass rules."""

    applicable = case["scoring"]["metrics_applicable"]

    for metric_name in BINARY_METRICS:
        if not applicable.get(metric_name, False):
            continue

        value = metrics.get(metric_name)

        if not isinstance(value, (int, float)) or value < 1.0:
            return False

    if applicable.get("gold_answer_match", False):
        value = metrics.get("gold_answer_match")

        if not isinstance(value, (int, float)):
            return False

        if case["scoring"]["match_mode"] == "status_match":
            if value < 1.0:
                return False

    return True


def metric_summary(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate scored metrics and pass rates."""

    aggregates: dict[str, Any] = {}

    for metric_name in METRIC_NAMES:
        values = [
            float(row["metrics"][metric_name])
            for row in rows
            if isinstance(
                row.get("metrics", {}).get(metric_name),
                (int, float),
            )
        ]

        aggregates[metric_name] = {
            "scored_cases": len(values),
            "mean": (
                round(mean(values), 4)
                if values
                else None
            ),
        }

    passed_count = sum(
        bool(row.get("passed"))
        for row in rows
    )

    aggregates["case_results"] = {
        "total": len(rows),
        "passed": passed_count,
        "failed": len(rows) - passed_count,
        "pass_rate": (
            round(passed_count / len(rows), 4)
            if rows
            else None
        ),
    }

    return aggregates


def latency_summary(
    rows: list[dict[str, Any]],
    representative_ids: set[str],
) -> dict[str, Any]:
    """Calculate p50 and p95 for representative cases."""

    selected = [
        row
        for row in rows
        if row["case_id"] in representative_ids
        and isinstance(
            row.get("metrics", {}).get("latency_ms"),
            (int, float),
        )
    ]

    all_values = [
        float(row["metrics"]["latency_ms"])
        for row in selected
    ]
    cold_values = [
        float(row["metrics"]["latency_ms"])
        for row in selected
        if row["metrics"].get("run_condition")
        == "cold_start"
    ]
    warm_values = [
        float(row["metrics"]["latency_ms"])
        for row in selected
        if row["metrics"].get("run_condition")
        == "warm"
    ]

    return {
        "representative_query_count": len(all_values),
        "p50_ms": percentile(all_values, 0.50),
        "p95_ms": percentile(all_values, 0.95),
        "cold_start": {
            "count": len(cold_values),
            "latencies_ms": cold_values,
        },
        "warm_start": {
            "count": len(warm_values),
            "p50_ms": percentile(warm_values, 0.50),
            "p95_ms": percentile(warm_values, 0.95),
        },
    }


def run_case(
    client,
    case: dict[str, Any],
    *,
    retrieval_top_k: int,
    run_condition: str,
) -> dict[str, Any]:
    """Submit one case through the same Flask chat endpoint."""

    payload = dict(case["request"])
    payload.update(
        {
            "evaluation_case_id": case["id"],
            "retrieval_top_k": retrieval_top_k,
            "run_condition": run_condition,
        }
    )

    response = client.post(
        "/chat",
        json=payload,
    )
    data = response.get_json() or {}

    metrics_event = next(
        (
            event
            for event in data.get("trace", [])
            if event.get("step") == "evaluation_metrics"
        ),
        None,
    )
    metrics = (
        metrics_event.get("metrics", {})
        if metrics_event
        else {}
    )

    passed = (
        response.status_code == 200
        and case_passed(case, metrics)
    )

    return {
        "case_id": case["id"],
        "title": case["title"],
        "category": case["category"],
        "retrieval_top_k": retrieval_top_k,
        "run_condition": run_condition,
        "http_status": response.status_code,
        "passed": passed,
        "answer": data.get("answer"),
        "citations": data.get("citations", []),
        "metrics": metrics,
        "trace": data.get("trace", []),
        "error": data.get("error"),
    }


def load_evaluation() -> dict[str, Any]:
    """Load the machine-readable Section 9 evaluation set."""

    return json.loads(
        EVALUATION_PATH.read_text(encoding="utf-8")
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run baseline, latency, or retrieval-k "
            "evaluation cases."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("baseline", "latency", "ablation"),
        default="baseline",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--output",
        type=Path,
    )
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        help=(
            "Run only the specified case ID. "
            "Repeat this option for multiple cases."
        ),
    )


    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.0,
        help=(
            "Seconds to wait between evaluation cases. "
            "Useful for free-tier API rate limits."
        ),
    )
    parser.add_argument(
        "--service-retries",
        type=int,
        default=0,
        help=(
            "Number of retries when policy RAG reports a "
            "service failure."
        ),
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=30.0,
        help=(
            "Base wait before retrying a policy-service failure. "
            "Each later retry multiplies this value."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not 1 <= args.top_k <= 10:
        raise SystemExit("--top-k must be between 1 and 10")

    if args.delay_seconds < 0:
        raise SystemExit("--delay-seconds cannot be negative")

    if args.service_retries < 0:
        raise SystemExit("--service-retries cannot be negative")

    if args.retry_backoff_seconds < 0:
        raise SystemExit(
            "--retry-backoff-seconds cannot be negative"
        )

    evaluation = load_evaluation()
    cases_by_id = {
        case["id"]: case
        for case in evaluation["cases"]
    }
    latency_ids = set(
        evaluation["latency_plan"][
            "representative_case_ids"
        ]
    )
    ablation_ids = evaluation["ablation_plan"]["case_ids"]

    if args.mode == "latency":
        selected_cases = [
            cases_by_id[case_id]
            for case_id in latency_ids
        ]
        top_k_values = [args.top_k]
    elif args.mode == "ablation":
        selected_cases = [
            cases_by_id[case_id]
            for case_id in ablation_ids
        ]
        top_k_values = [3, 5]
    else:
        selected_cases = evaluation["cases"]
        top_k_values = [args.top_k]

    if args.case_ids:
        unknown_ids = [
            case_id
            for case_id in args.case_ids
            if case_id not in cases_by_id
        ]

        if unknown_ids:
            raise SystemExit(
                "Unknown evaluation case IDs: "
                + ", ".join(unknown_ids)
            )

        selected_cases = [
            cases_by_id[case_id]
            for case_id in args.case_ids
        ]

    client = app.test_client()
    rows: list[dict[str, Any]] = []

    total_runs = len(selected_cases) * len(top_k_values)
    run_number = 0

    for top_k in top_k_values:
        for case_index, case in enumerate(selected_cases):
            run_number += 1

            if args.mode == "ablation":
                condition = f"ablation_k{top_k}"
            elif case_index == 0:
                condition = "cold_start"
            else:
                condition = "warm"

            print(
                f"[{run_number}/{total_runs}] "
                f"{case['id']} top_k={top_k}",
                flush=True,
            )

            if (
                run_number > 1
                and args.delay_seconds > 0
            ):
                print(
                    f"  Waiting {args.delay_seconds:g} seconds "
                    "for API pacing",
                    flush=True,
                )
                time.sleep(args.delay_seconds)

            attempt = 0

            while True:
                row = run_case(
                    client,
                    case,
                    retrieval_top_k=top_k,
                    run_condition=condition,
                )

                service_failed = any(
                    event.get("step")
                    == "policy_retrieval_and_answering"
                    and event.get("status") == "failed"
                    for event in row.get("trace", [])
                )

                if (
                    not service_failed
                    or attempt >= args.service_retries
                ):
                    break

                attempt += 1
                wait_seconds = (
                    args.retry_backoff_seconds
                    * attempt
                )

                print(
                    "  Policy service failed; "
                    f"retry {attempt} of "
                    f"{args.service_retries} after "
                    f"{wait_seconds:g} seconds",
                    flush=True,
                )
                time.sleep(wait_seconds)

            rows.append(row)

            print(
                "  "
                + (
                    "PASS"
                    if row["passed"]
                    else "FAIL"
                ),
                flush=True,
            )

    summary: dict[str, Any] = {
        "overall": metric_summary(rows),
        "latency": latency_summary(
            rows,
            latency_ids,
        ),
    }

    if args.mode == "ablation":
        by_top_k: dict[str, Any] = {}

        for top_k in top_k_values:
            selected_rows = [
                row
                for row in rows
                if row["retrieval_top_k"] == top_k
            ]
            by_top_k[str(top_k)] = {
                "metrics": metric_summary(selected_rows),
                "latency": latency_summary(
                    selected_rows,
                    set(ablation_ids),
                ),
            }

        summary["ablation_by_top_k"] = by_top_k

    output_path = args.output or (
        PROJECT_ROOT
        / "evaluation"
        / "results"
        / f"section9_{args.mode}_results.json"
    )
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "evaluation_name": evaluation["evaluation_name"],
        "schema_version": evaluation["schema_version"],
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "mode": args.mode,
        "summary": summary,
        "results": rows,
    }

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"\nResults written to {output_path}")
    print(
        json.dumps(
            summary,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
