"""Deterministic safety and escalation rules for policy requests."""

from __future__ import annotations


SENSITIVE_DATA_TERMS = (
    "personal email",
    "personal phone",
    "home address",
    "salary",
    "compensation",
    "social security",
    "bank account",
)

DISCLOSURE_TERMS = (
    "tell me",
    "show me",
    "give me",
    "list",
    "provide",
    "reveal",
    "ignore your policies",
)


def is_sensitive_data_request(message: str) -> bool:
    """Identify requests to disclose sensitive employee data."""

    normalized = " ".join(message.casefold().split())

    has_sensitive_term = any(
        term in normalized
        for term in SENSITIVE_DATA_TERMS
    )
    has_disclosure_term = any(
        term in normalized
        for term in DISCLOSURE_TERMS
    )

    return has_sensitive_term and has_disclosure_term


def build_sensitive_policy_question() -> str:
    """Create a retrieval query focused on privacy policy."""

    return (
        "Using Northstar Analytics information-security, "
        "data-classification, acceptable-use, and employee-handbook "
        "policies, explain the restrictions on disclosing personnel "
        "data, personal contact information, home addresses, and "
        "compensation. Explain that access requires authorization "
        "and an approved business process. Do not disclose any "
        "employee-specific information."
    )


def build_sensitive_refusal() -> str:
    """Return a deterministic privacy-preserving response."""

    return (
        "I cannot disclose or retrieve an employee's personal "
        "contact information, home address, compensation, or other "
        "sensitive personnel data for this request. Northstar "
        "requires authorization and an approved business process "
        "for access to personnel information [Source 1]. For a "
        "legitimate employment-data need, contact People Operations "
        "through an authorized channel."
    )


def requires_policy_escalation(message: str) -> bool:
    """Identify policy scenarios requiring operational escalation."""

    normalized = " ".join(message.casefold().split())

    border_incident = (
        "border" in normalized
        and any(
            term in normalized
            for term in (
                "searched",
                "seized",
                "inspected",
            )
        )
    )

    leave_review_concern = (
        any(
            term in normalized
            for term in (
                "approved medical leave",
                "protected leave",
            )
        )
        and any(
            term in normalized
            for term in (
                "review",
                "rating",
                "lower",
                "manager",
                "retaliation",
            )
        )
    )

    surgery_leave = (
        "surgery" in normalized
        and any(
            term in normalized
            for term in (
                "pto",
                "days off",
                "medical leave",
            )
        )
    )

    return (
        border_incident
        or leave_review_concern
        or surgery_leave
    )
