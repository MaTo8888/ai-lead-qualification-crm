"""Final qualification decision: deterministic business signals + the AI
(or fallback) opinion, combined — not the AI output taken at face value.

The signals below are plain booleans/short labels, not invented 0-100
confidence scores; each one maps to something actually present in the
lead's own data, so the final category stays explainable.
"""

from typing import Any

from app.constants import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    QUALIFICATION_HOT,
    QUALIFICATION_LOW_PRIORITY,
    QUALIFICATION_UNQUALIFIED,
    QUALIFICATION_WARM,
    QUALIFICATIONS,
    PRIORITIES,
)

URGENT_TIMELINE_WORDS = ["immediately", "asap", "this week", "urgent", "days"]
LARGE_COMPANY_HINTS = ["200", "500", "1000", "large", "enterprise"]


def deterministic_signals(lead: dict[str, Any]) -> dict[str, bool]:
    """Indicators derived directly from the raw lead fields — no AI involved."""
    budget = (lead.get("estimated_budget") or "").strip().lower()
    timeline = (lead.get("timeline") or "").strip().lower()
    message = (lead.get("message") or "").strip()
    company_size = (lead.get("company_size") or "").strip().lower()

    return {
        "has_budget": bool(budget) and budget not in ("no budget", "none", "0", "tbd", "not sure yet"),
        "has_urgent_timeline": any(w in timeline for w in URGENT_TIMELINE_WORDS),
        "has_clear_message": len(message) >= 20,
        "is_b2b_context": bool(lead.get("company")),
        "is_large_company": any(w in company_size for w in LARGE_COMPANY_HINTS),
    }


def combine_qualification(ai_result: dict[str, Any], signals: dict[str, bool]) -> dict[str, Any]:
    """Takes the AI's proposed qualification/priority and adjusts it against
    deterministic signals when they clearly disagree. Documented, small
    adjustments only — this is not a second independent classifier.
    """
    qualification = ai_result.get("qualification")
    priority = ai_result.get("priority")

    if qualification not in QUALIFICATIONS:
        qualification = QUALIFICATION_LOW_PRIORITY
    if priority not in PRIORITIES:
        priority = PRIORITY_MEDIUM

    signal_count = sum([
        signals["has_budget"],
        signals["has_urgent_timeline"],
        signals["has_clear_message"],
        signals["is_b2b_context"],
    ])

    # AI said HOT but almost nothing in the raw data actually supports urgency
    # or budget — pull it back to WARM rather than trusting the claim blindly.
    if qualification == QUALIFICATION_HOT and not (signals["has_budget"] or signals["has_urgent_timeline"]):
        qualification = QUALIFICATION_WARM
        priority = PRIORITY_MEDIUM

    # AI said UNQUALIFIED/LOW_PRIORITY but the raw data shows strong signals
    # across the board (budget + urgent timeline + real company context) —
    # flag for a human instead of silently discarding a possibly good lead.
    elif qualification in (QUALIFICATION_UNQUALIFIED, QUALIFICATION_LOW_PRIORITY) and signal_count >= 3:
        qualification = QUALIFICATION_WARM
        priority = PRIORITY_MEDIUM
        ai_result = {**ai_result, "recommended_action": "Manual review"}

    # Large company + urgent timeline is worth a priority bump even at WARM.
    if qualification == QUALIFICATION_WARM and signals["is_large_company"] and signals["has_urgent_timeline"]:
        priority = PRIORITY_HIGH

    return {
        **ai_result,
        "qualification": qualification,
        "priority": priority,
    }
