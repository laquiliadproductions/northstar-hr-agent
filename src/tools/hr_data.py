"""Safe, read-only access to Northstar HR data."""

from __future__ import annotations
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROSTER_PATH = (
    PROJECT_ROOT
    / "data"
    / "structured"
    / "Northstar_Analytics_Employee_Roster.csv"
)

REQUIRED_ROSTER_COLUMNS = {
    "First Name",
    "Last Name",
    "Email Address",
    "Start Date",
    "Job Title",
    "Department",
    "Hourly/Salary",
    "Office Location",
    "Remote/Hybrid",
    "Address: Country",
    "US/International",
    "Management Level",
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

def _load_roster(path: Path = ROSTER_PATH) -> pd.DataFrame:
    """Load the roster and validate the columns used by HR tools."""

    roster = pd.read_csv(path, skiprows=3, encoding="cp1250")
    missing_columns = REQUIRED_ROSTER_COLUMNS.difference(roster.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Roster is missing required columns: {missing}")

    return roster

def _employee_view(row: pd.Series) -> dict[str, Any]:
    """Return only fields needed for supported HR workflows."""

    return {
        "first_name": _clean_value(row["First Name"]),
        "last_name": _clean_value(row["Last Name"]),
        "work_email": _clean_value(row["Email Address"]),
        "start_date": _clean_value(row["Start Date"]),
        "job_title": _clean_value(row["Job Title"]),
        "department": _clean_value(row["Department"]),
        "employment_type": _clean_value(row["Hourly/Salary"]),
        "office_location": _clean_value(row["Office Location"]),
        "work_arrangement": _clean_value(row["Remote/Hybrid"]),
        "country": _clean_value(row["Address: Country"]),
        "us_international": _clean_value(row["US/International"]),
        "management_level": _clean_value(row["Management Level"]),
    }

def lookup_employee(
    work_email: str | None = None,
    full_name: str | None = None,
) -> dict[str, Any]:

    """Find one employee by work email or exact full name."""
    normalized_email = (work_email or "").strip().casefold()
    normalized_name = (full_name or "").strip().casefold()

    if not normalized_email and not normalized_name:
        return {
            "status": "needs_clarification",
            "message": (
                "Provide the employee's work email or exact full name."
            ),
        }

    try:
        roster = _load_roster()
    except (FileNotFoundError, OSError, ValueError, pd.errors.ParserError) as exc:
        return {
            "status": "unavailable",
            "message": "The employee roster is currently unavailable.",
            "error_type": type(exc).__name__,
        }

    if normalized_email:
        values = (
            roster["Email Address"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )
        matches = roster.loc[values == normalized_email]
        lookup_description = work_email

    else:
        names = (
            roster["First Name"].fillna("").astype(str).str.strip()
            + " "
            + roster["Last Name"].fillna("").astype(str).str.strip()
        ).str.casefold()
        matches = roster.loc[names == normalized_name]
        lookup_description = full_name

    if matches.empty:
        return {
            "status": "not_found",
            "message": f"No employee matched {lookup_description!r}.",
        }

    if len(matches) > 1:
        candidates = [
            {
                "full_name": (
                    f"{_clean_value(row['First Name'])} "
                    f"{_clean_value(row['Last Name'])}"
                ),
                "work_email": _clean_value(row["Email Address"]),
            }

            for _, row in matches.iterrows()
        ]

        return {
            "status": "needs_clarification",
            "message": "Multiple employees matched. Provide a work email.",
            "candidates": candidates,
        }

    return {
        "status": "ok",
        "employee": _employee_view(matches.iloc[0]),
    }
