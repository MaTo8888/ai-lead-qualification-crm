"""Real duplicate detection against the CRM — email and phone, checked
against whatever is already stored in SQLite. Never overwrites an existing
record; it only classifies the new one so the pipeline (and a human, if
needed) can decide what to do with it.
"""

from typing import Any, Optional

from app import db
from app.constants import DUPLICATE_EXISTING, DUPLICATE_NEW, DUPLICATE_POSSIBLE


def check_duplicate(email: str, phone: str) -> tuple[str, Optional[str]]:
    """Returns (duplicate_status, duplicate_of_lead_id)."""
    email_matches = db.find_by_email(email) if email else []
    if email_matches:
        return DUPLICATE_EXISTING, email_matches[0]["lead_id"]

    phone_digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    phone_matches = db.find_by_phone(phone_digits) if phone_digits else []
    if phone_matches:
        return DUPLICATE_POSSIBLE, phone_matches[0]["lead_id"]

    return DUPLICATE_NEW, None
