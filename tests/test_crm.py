from app import db


def test_insert_and_get_lead():
    db.insert_lead({
        "lead_id": "LEAD-t1", "created_at": "2026-01-01T00:00:00", "email": "a@example.com",
        "status": "COMPLETED", "qualification": "HOT",
    })
    lead = db.get_lead("LEAD-t1")
    assert lead is not None
    assert lead["email"] == "a@example.com"
    assert lead["qualification"] == "HOT"


def test_get_unknown_lead_returns_none():
    assert db.get_lead("LEAD-does-not-exist") is None


def test_update_lead():
    db.insert_lead({"lead_id": "LEAD-t2", "created_at": "2026-01-01T00:00:00", "status": "PROCESSING"})
    db.update_lead("LEAD-t2", {"status": "COMPLETED", "qualification": "WARM"})
    lead = db.get_lead("LEAD-t2")
    assert lead["status"] == "COMPLETED"
    assert lead["qualification"] == "WARM"


def test_list_leads_filters_by_qualification():
    db.insert_lead({"lead_id": "LEAD-t3", "created_at": "2026-01-01T00:00:00", "qualification": "HOT", "status": "COMPLETED"})
    db.insert_lead({"lead_id": "LEAD-t4", "created_at": "2026-01-01T00:00:00", "qualification": "WARM", "status": "COMPLETED"})
    hot_leads = db.list_leads(qualification="HOT")
    assert len(hot_leads) == 1
    assert hot_leads[0]["lead_id"] == "LEAD-t3"


def test_validation_errors_round_trip_as_list():
    db.insert_lead({
        "lead_id": "LEAD-t5", "created_at": "2026-01-01T00:00:00", "status": "VALIDATION_FAILED",
        "validation_errors": ["Email is required.", "Message is required."],
    })
    lead = db.get_lead("LEAD-t5")
    assert lead["validation_errors"] == ["Email is required.", "Message is required."]


def test_insert_and_list_handoffs():
    db.insert_handoff({
        "handoff_id": "HANDOFF-t1", "lead_id": "LEAD-t1", "created_at": "2026-01-01T00:00:00",
        "company": "Acme", "qualification": "HOT", "priority": "HIGH", "channel": "internal_queue",
        "delivery_status": "QUEUED",
    })
    handoffs = db.list_handoffs()
    assert len(handoffs) == 1
    assert handoffs[0]["handoff_id"] == "HANDOFF-t1"
