"""Safe, read-only access to Northstar PTO balance data."""

from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PTO_BALANCES_PATH = (
    PROJECT_ROOT
    / "data"
    / "structured"
    / "Northstar_Analytics_PTO_Balances.csv"
)

REQUIRED_PTO_COLUMNS = {
    "Employee ID",
    "First Name",
    "Last Name",
    "Email Address",
    "Annual PTO Allowance (Days)",
    "Carryover (Days)",
    "Accrued YTD (Days)",
    "Used YTD (Days)",
    "Pending Requests (Days)",
    "Current Balance (Days)",
    "Available After Pending (Days)",
    "As of Date",
}

def _clean_value(value: Any) -> Any:
    """Convert pandas values into JSON-friendly Python values."""

    if pd.isna(value):
        return None

    if isinstance(value, str):
        return value.strip()

    if hasattr(value, "item"):
        return value.item()

    return value

def _load_pto_balances(
    path: Path = PTO_BALANCES_PATH,
) -> pd.DataFrame:
    """Load PTO balances and validate the required schema."""

    balances = pd.read_csv(path, skiprows=7, encoding="utf-8")

    missing_columns = REQUIRED_PTO_COLUMNS.difference(balances.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"PTO balance file is missing required columns: {missing}"
        )

    return balances

def _pto_balance_view(row: pd.Series) -> dict[str, Any]:
    """Return the fields needed for PTO guidance."""

    return {
        "employee_id": _clean_value(row["Employee ID"]),
        "first_name": _clean_value(row["First Name"]),
        "last_name": _clean_value(row["Last Name"]),
        "work_email": _clean_value(row["Email Address"]),
        "annual_allowance_days": _clean_value(
            row["Annual PTO Allowance (Days)"]
        ),
        "carryover_days": _clean_value(row["Carryover (Days)"]),
        "accrued_ytd_days": _clean_value(row["Accrued YTD (Days)"]),
        "used_ytd_days": _clean_value(row["Used YTD (Days)"]),
        "pending_request_days": _clean_value(
            row["Pending Requests (Days)"]
        ),
        "current_balance_days": _clean_value(
            row["Current Balance (Days)"]
        ),
        "available_after_pending_days": _clean_value(
            row["Available After Pending (Days)"]
        ),
        "as_of_date": _clean_value(row["As of Date"]),
    }

def get_pto_balance(
    employee_id: str | None = None,
    work_email: str | None = None,
) -> dict[str, Any]:
    """Find one employee's PTO balance by ID or work email."""

    normalized_id = (employee_id or "").strip().casefold()
    normalized_email = (work_email or "").strip().casefold()

    if not normalized_id and not normalized_email:
        return {
            "status": "needs_clarification",
            "message": "Provide an employee ID or work email.",
        }

    try:
        balances = _load_pto_balances()
    except (
        FileNotFoundError,
        OSError,
        ValueError,
        pd.errors.ParserError,
    ) as exc:

        return {
            "status": "unavailable",
            "message": "PTO balance data is currently unavailable.",
            "error_type": type(exc).__name__,
        }

    if normalized_id:
        values = (
            balances["Employee ID"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        matches = balances.loc[values == normalized_id]
        lookup_description = employee_id

    else:
        values = (
            balances["Email Address"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        matches = balances.loc[values == normalized_email]
        lookup_description = work_email



    if matches.empty:
        return {
            "status": "not_found",
            "message": f"No PTO balance matched {lookup_description!r}.",
        }

    if len(matches) > 1:
        return {
            "status": "needs_clarification",
            "message": (
                "Multiple PTO records matched. Provide the employee ID."
            ),
        }

    return {
        "status": "ok",
        "pto_balance": _pto_balance_view(matches.iloc[0]),
    }
