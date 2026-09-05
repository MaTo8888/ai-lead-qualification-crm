from app import db
from app.constants import DUPLICATE_EXISTING, DUPLICATE_NEW, DUPLICATE_POSSIBLE
from app.duplicate_check import check_duplicate


def _insert_existing(email="anna@example.com", phone="+49 89 5551234"):
    db.insert_lead({
        "lead_id": "LEAD-existing1", "created_at": "2026-01-01T00:00:00", "email": email,
        "phone": phone, "status": "COMPLETED",
    })


def test_new_lead_has_no_match():
    status, duplicate_of = check_duplicate("fresh@example.com", "+49 30 0000000")
    assert status == DUPLICATE_NEW
    assert duplicate_of is None


def test_same_email_is_existing_lead():
    _insert_existing()
    status, duplicate_of = check_duplicate("anna@example.com", "+49 99 9999999")
    assert status == DUPLICATE_EXISTING
    assert duplicate_of == "LEAD-existing1"


def test_email_match_is_case_insensitive():
    _insert_existing(email="anna@example.com")
    status, _ = check_duplicate("ANNA@EXAMPLE.COM", "")
    assert status == DUPLICATE_EXISTING


def test_same_phone_different_email_is_possible_duplicate():
    _insert_existing(phone="+49 89 5551234")
    status, duplicate_of = check_duplicate("different@example.com", "+49 89 5551234")
    assert status == DUPLICATE_POSSIBLE
    assert duplicate_of == "LEAD-existing1"
