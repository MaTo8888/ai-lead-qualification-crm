"""End-to-end pipeline tests through the real HTTP API (FastAPI TestClient)."""

VALID_HOT_LEAD = {
    "first_name": "Anna", "last_name": "Becker", "company": "Nordstern GmbH",
    "email": "anna.becker@example.com", "phone": "+49 89 5551234",
    "company_size": "80 employees", "industry": "Industrial Equipment",
    "message": "We urgently need to automate our incoming service inquiries, budget is approved.",
    "estimated_budget": "15000 EUR", "timeline": "urgent, this week",
}

VALID_WARM_LEAD = {
    "first_name": "Jonas", "last_name": "Weller", "company": "Bergfried Consulting",
    "email": "jonas.weller@example.com",
    "message": "We are looking into automating lead handling at some point this year.",
    "estimated_budget": "5000 EUR", "timeline": "next quarter",
}

UNQUALIFIED_LEAD = {
    "first_name": "Spam", "email": "offers@spam.example",
    "message": "Buy our cheap SEO package and backlink service now!",
}

INVALID_LEAD = {"first_name": "Peter", "email": "not-an-email", "message": "hi"}


def test_valid_hot_lead_completes_and_creates_handoff(client):
    response = client.post("/api/leads", json=VALID_HOT_LEAD)
    assert response.status_code == 200
    lead = response.json()
    assert lead["status"] == "COMPLETED"
    assert lead["qualification"] == "HOT"
    assert lead["duplicate_status"] == "NEW"

    handoffs = client.get("/api/handoffs").json()
    assert any(h["lead_id"] == lead["lead_id"] for h in handoffs)


def test_warm_lead_completes(client):
    response = client.post("/api/leads", json=VALID_WARM_LEAD)
    assert response.status_code == 200
    lead = response.json()
    assert lead["status"] == "COMPLETED"
    assert lead["qualification"] in ("WARM", "HOT")


def test_unqualified_lead_gets_no_handoff(client):
    response = client.post("/api/leads", json=UNQUALIFIED_LEAD)
    lead = response.json()
    assert lead["qualification"] == "UNQUALIFIED"

    handoffs = client.get("/api/handoffs").json()
    assert not any(h["lead_id"] == lead["lead_id"] for h in handoffs)


def test_invalid_lead_returns_validation_failed(client):
    response = client.post("/api/leads", json=INVALID_LEAD)
    assert response.status_code == 200
    lead = response.json()
    assert lead["status"] == "VALIDATION_FAILED"
    assert lead["validation_errors"]


def test_duplicate_lead_is_detected(client):
    first = client.post("/api/leads", json=VALID_HOT_LEAD).json()
    second = client.post("/api/leads", json=VALID_HOT_LEAD).json()
    assert first["lead_id"] != second["lead_id"]
    assert second["duplicate_status"] == "EXISTING_LEAD"
    assert second["duplicate_of"] == first["lead_id"]


def test_get_leads_lists_created_leads(client):
    client.post("/api/leads", json=VALID_HOT_LEAD)
    response = client.get("/api/leads")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_leads_filters_by_qualification(client):
    client.post("/api/leads", json=VALID_HOT_LEAD)
    client.post("/api/leads", json=UNQUALIFIED_LEAD)
    response = client.get("/api/leads", params={"qualification": "HOT"})
    assert all(lead["qualification"] == "HOT" for lead in response.json())


def test_get_unknown_lead_returns_404(client):
    response = client.get("/api/leads/LEAD-does-not-exist")
    assert response.status_code == 404


def test_get_leads_invalid_filter_returns_400(client):
    response = client.get("/api/leads", params={"qualification": "SUPER_HOT"})
    assert response.status_code == 400


def test_stats_endpoint_reflects_created_leads(client):
    client.post("/api/leads", json=VALID_HOT_LEAD)
    client.post("/api/leads", json=UNQUALIFIED_LEAD)
    stats = client.get("/api/stats").json()
    assert stats["total_leads"] >= 2
    assert "HOT" in stats["by_qualification"] or "UNQUALIFIED" in stats["by_qualification"]
