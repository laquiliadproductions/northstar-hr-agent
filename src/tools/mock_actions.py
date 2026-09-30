"""Confirmation-gated mock HR actions."""

from __future__ import annotations
from datetime import date
from typing import Any
from uuid import uuid4

def mock_submit_pto_request(
    employee_id: str | None,
    start_date: str | None,
    end_date: str | None,
    requested_days: float | None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Preview or simulate a PTO request without changing HR records."""

    if not employee_id:
        return {
            "status": "needs_clarification",
            "message": "An employee ID is required.",
        }

    if not start_date or not end_date:
        return {
            "status": "needs_clarification",
            "message": "Both a start date and end date are required.",
        }

    if requested_days is None:
        return {
            "status": "needs_clarification",
            "message": "The number of requested PTO days is required.",
        }

    if requested_days <= 0:
        return {
            "status": "invalid_request",
            "message": "Requested PTO days must be greater than zero.",
        }

    try:
        parsed_start = date.fromisoformat(start_date)
        parsed_end = date.fromisoformat(end_date)
    except ValueError:
        return {
            "status": "invalid_request",
            "message": "Dates must use YYYY-MM-DD format.",
        }

    if parsed_end < parsed_start:
        return {
            "status": "invalid_request",
            "message": "The end date cannot be before the start date.",
        }

    preview = {
        "employee_id": employee_id.strip().upper(),
        "start_date": parsed_start.isoformat(),
        "end_date": parsed_end.isoformat(),
        "requested_days": float(requested_days),
    }

    if not confirmed:
        return {
            "status": "confirmation_required",
            "message": (
                "Review the request and explicitly confirm before "
                "running the mock submission."
            ),
            "preview": preview,
            "side_effects": "none",
        }

    return {
        "status": "mock_completed",
        "message": (
            "Mock PTO request completed. No HR system or employee "
            "record was changed."
        ),
        "mock_request_id": f"MOCK-PTO-{uuid4().hex[:8].upper()}",
        "request": preview,
        "side_effects": "none",
    }
