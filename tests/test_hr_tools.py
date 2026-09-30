"""Tests for the read-only HR data tools."""

from src.tools.hr_data import lookup_employee
from src.tools.pto_data import get_pto_balance

def test_lookup_employee_by_email() -> None:
    result = lookup_employee(
        work_email="MAYA.CHEN@NORTHSTARANALYTICS.COM"
    )

    assert result["status"] == "ok"
    assert result["employee"]["first_name"] == "Maya"
    assert result["employee"]["work_email"] == (
        "maya.chen@northstaranalytics.com"
    )

def test_employee_lookup_excludes_sensitive_fields() -> None:
    result = lookup_employee(
        work_email="maya.chen@northstaranalytics.com"
    )

    employee = result["employee"]

    assert "Annual Salary" not in employee
    assert "Personal Email" not in employee
    assert "Personal Phone" not in employee
    assert "Address: Street" not in employee

def test_employee_lookup_requires_identifier() -> None:
    result = lookup_employee()

    assert result["status"] == "needs_clarification"

def test_get_pto_balance_by_employee_id() -> None:
    result = get_pto_balance(employee_id="nsa-0001")

    assert result["status"] == "ok"
    assert result["pto_balance"]["employee_id"] == "NSA-0001"
    assert result["pto_balance"]["available_after_pending_days"] == 16.9

def test_get_pto_balance_requires_identifier() -> None:
    result = get_pto_balance()

    assert result["status"] == "needs_clarification"

def test_get_pto_balance_handles_unknown_employee() -> None:
    result = get_pto_balance(employee_id="NSA-9999")

    assert result["status"] == "not_found"
