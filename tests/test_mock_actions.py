"""Tests for confirmation-gated mock actions."""

from src.tools.mock_actions import mock_submit_pto_request

def test_pto_request_requires_confirmation() -> None:
    result = mock_submit_pto_request(
        employee_id="NSA-0001",
        start_date="2026-10-12",
        end_date="2026-10-14",
        requested_days=3.0,
    )

    assert result["status"] == "confirmation_required"
    assert result["side_effects"] == "none"
    assert "mock_request_id" not in result

def test_confirmed_pto_request_remains_mock() -> None:
    result = mock_submit_pto_request(
        employee_id="NSA-0001",
        start_date="2026-10-12",
        end_date="2026-10-14",
        requested_days=3.0,
        confirmed=True,
    )

    assert result["status"] == "mock_completed"
    assert result["mock_request_id"].startswith("MOCK-PTO-")
    assert result["side_effects"] == "none"

def test_pto_request_rejects_invalid_date_range() -> None:
    result = mock_submit_pto_request(
        employee_id="NSA-0001",
        start_date="2026-10-14",
        end_date="2026-10-12",
        requested_days=3.0,
        confirmed=True,
    )

    assert result["status"] == "invalid_request"
    assert "mock_request_id" not in result
