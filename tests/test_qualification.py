from app.constants import (
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    QUALIFICATION_HOT,
    QUALIFICATION_UNQUALIFIED,
    QUALIFICATION_WARM,
)
from app.qualification import combine_qualification, deterministic_signals


def test_signals_detect_budget_and_urgency():
    signals = deterministic_signals({
        "estimated_budget": "10000 EUR", "timeline": "urgent, this week",
        "message": "We need help automating our lead intake process.",
        "company": "Acme GmbH", "company_size": "500 employees",
    })
    assert signals["has_budget"] is True
    assert signals["has_urgent_timeline"] is True
    assert signals["has_clear_message"] is True
    assert signals["is_b2b_context"] is True
    assert signals["is_large_company"] is True


def test_signals_detect_absence_of_budget():
    signals = deterministic_signals({"estimated_budget": "no budget", "timeline": "", "message": "", "company": ""})
    assert signals["has_budget"] is False
    assert signals["has_urgent_timeline"] is False
    assert signals["is_b2b_context"] is False


def test_hot_without_support_is_pulled_back_to_warm():
    ai_result = {"qualification": QUALIFICATION_HOT, "priority": PRIORITY_HIGH}
    signals = {"has_budget": False, "has_urgent_timeline": False, "has_clear_message": True,
               "is_b2b_context": True, "is_large_company": False}
    result = combine_qualification(ai_result, signals)
    assert result["qualification"] == QUALIFICATION_WARM
    assert result["priority"] == PRIORITY_MEDIUM


def test_hot_with_support_stays_hot():
    ai_result = {"qualification": QUALIFICATION_HOT, "priority": PRIORITY_HIGH}
    signals = {"has_budget": True, "has_urgent_timeline": True, "has_clear_message": True,
               "is_b2b_context": True, "is_large_company": False}
    result = combine_qualification(ai_result, signals)
    assert result["qualification"] == QUALIFICATION_HOT
    assert result["priority"] == PRIORITY_HIGH


def test_unqualified_with_strong_signals_flagged_for_review():
    ai_result = {"qualification": QUALIFICATION_UNQUALIFIED, "priority": "LOW", "recommended_action": "No immediate action"}
    signals = {"has_budget": True, "has_urgent_timeline": True, "has_clear_message": True,
               "is_b2b_context": True, "is_large_company": False}
    result = combine_qualification(ai_result, signals)
    assert result["qualification"] == QUALIFICATION_WARM
    assert result["recommended_action"] == "Manual review"


def test_large_company_urgent_warm_gets_priority_bump():
    ai_result = {"qualification": QUALIFICATION_WARM, "priority": PRIORITY_MEDIUM}
    signals = {"has_budget": True, "has_urgent_timeline": True, "has_clear_message": True,
               "is_b2b_context": True, "is_large_company": True}
    result = combine_qualification(ai_result, signals)
    assert result["qualification"] == QUALIFICATION_WARM
    assert result["priority"] == PRIORITY_HIGH


def test_invalid_ai_categories_are_normalized():
    ai_result = {"qualification": "SUPER_HOT", "priority": "CRITICAL"}
    signals = {"has_budget": False, "has_urgent_timeline": False, "has_clear_message": False,
               "is_b2b_context": False, "is_large_company": False}
    result = combine_qualification(ai_result, signals)
    assert result["qualification"] in ("LOW_PRIORITY",)
    assert result["priority"] == PRIORITY_MEDIUM
