"""Business-rule validation and normalization for incoming leads.

Runs before anything else in the pipeline. A lead that fails here never
reaches duplicate check, AI analysis, or the CRM as a qualified record —
it is still stored (for auditability) with status VALIDATION_FAILED and
a human-readable list of reasons.
"""

import re
from typing import Any

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_MESSAGE_LENGTH = 5


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_lead(raw: dict[str, Any]) -> dict[str, Any]:
    """Trims whitespace, collapses internal whitespace, lowercases the email."""
    normalized = {k: _clean(v) for k, v in raw.items()}
    normalized["email"] = normalized.get("email", "").lower()
    return normalized


def validate_lead(raw: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    """Returns (is_valid, errors, normalized_data)."""
    data = normalize_lead(raw)
    errors: list[str] = []

    if not data.get("email"):
        errors.append("Email is required.")
    elif not EMAIL_RE.match(data["email"]):
        errors.append(f"Email address is not valid: '{data['email']}'.")

    if not data.get("message"):
        errors.append("Message is required.")
    elif len(data["message"]) < MIN_MESSAGE_LENGTH:
        errors.append("Message is too short to be a meaningful inquiry.")

    has_name = bool(data.get("first_name") or data.get("last_name"))
    has_company = bool(data.get("company"))
    if not has_name and not has_company:
        errors.append("At least a name or a company is required to identify the lead.")

    if data.get("phone"):
        digits = "".join(ch for ch in data["phone"] if ch.isdigit())
        if len(digits) < 6:
            errors.append(f"Phone number looks invalid: '{data['phone']}'.")

    return (len(errors) == 0, errors, data)
