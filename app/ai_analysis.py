"""AI analysis step: produces a structured first-pass read of the lead.

Tries a real LLM first (Anthropic, then OpenAI — whichever key is present
in this project's own .env). If no key is configured, the request fails,
or the model returns something that isn't valid structured JSON, it falls
back to a deterministic, keyword-based analyzer so the pipeline never
stalls. Every result carries `analysis_mode` ("ai" or "fallback_rules") so
downstream views can be honest about which one actually ran.

This step's output is a *first-pass opinion*, not the final word — see
qualification.py, which combines it with deterministic business signals
before anything is written to the CRM as final qualification/priority.
"""

import json
import logging
import os
import re
from typing import Any

from app.constants import (
    ANALYSIS_MODE_AI,
    ANALYSIS_MODE_FALLBACK,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    QUALIFICATION_HOT,
    QUALIFICATION_LOW_PRIORITY,
    QUALIFICATION_UNQUALIFIED,
    QUALIFICATION_WARM,
)

log = logging.getLogger("lead_pipeline")

REQUIRED_KEYS = [
    "intent", "summary", "qualification", "priority",
    "potential_fit", "urgency", "recommended_action",
]

SYSTEM_PROMPT = """You are a B2B sales lead analyst. Given a lead's inquiry, \
return ONLY a JSON object (no prose, no markdown fences) with exactly these keys:
intent (short phrase, e.g. "Process Automation"),
summary (1-2 sentences, professional, based only on the information given),
qualification (one of: HOT, WARM, LOW_PRIORITY, UNQUALIFIED),
priority (one of: HIGH, MEDIUM, LOW),
potential_fit (short phrase, e.g. "Strong fit" / "Unclear fit" / "Poor fit"),
urgency (one of: High, Medium, Low),
recommended_action (short actionable phrase, e.g. "Call within 1 hour").
Never invent company facts that were not provided."""


def analyze_lead(lead: dict[str, Any]) -> dict[str, Any]:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if anthropic_key:
        try:
            return _analyze_with_anthropic(lead, anthropic_key)
        except Exception as exc:  # noqa: BLE001 - any provider failure must fall back, not crash the pipeline
            log.warning("Anthropic analysis failed, falling back: %s", type(exc).__name__)

    if openai_key:
        try:
            return _analyze_with_openai(lead, openai_key)
        except Exception as exc:  # noqa: BLE001
            log.warning("OpenAI analysis failed, falling back: %s", type(exc).__name__)

    return _analyze_with_fallback(lead)


def _lead_prompt(lead: dict[str, Any]) -> str:
    return (
        f"Company: {lead.get('company') or 'unknown'}\n"
        f"Company size: {lead.get('company_size') or 'unknown'}\n"
        f"Industry: {lead.get('industry') or 'unknown'}\n"
        f"Estimated budget: {lead.get('estimated_budget') or 'not provided'}\n"
        f"Timeline: {lead.get('timeline') or 'not provided'}\n"
        f"Source: {lead.get('source') or 'unknown'}\n"
        f"Message: {lead.get('message') or ''}"
    )


def _parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    data = json.loads(text)
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"AI response missing keys: {missing}")
    return data


def _analyze_with_anthropic(lead: dict[str, Any], api_key: str) -> dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _lead_prompt(lead)}],
    )
    raw_text = "".join(block.text for block in response.content if hasattr(block, "text"))
    data = _parse_json_response(raw_text)
    data["analysis_mode"] = ANALYSIS_MODE_AI
    return data


def _analyze_with_openai(lead: dict[str, Any], api_key: str) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=400,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _lead_prompt(lead)},
        ],
    )
    raw_text = response.choices[0].message.content or ""
    data = _parse_json_response(raw_text)
    data["analysis_mode"] = ANALYSIS_MODE_AI
    return data


# ── Deterministic fallback ──────────────────────────────────────────────
# No scored 0-100 confidence numbers — just transparent keyword signals
# that map onto the same fixed categories a real model would return.

URGENT_WORDS = ["urgent", "asap", "immediately", "as soon as possible", "right away", "dringend"]
LOW_INTENT_WORDS = ["just curious", "just browsing", "no rush", "someday", "maybe later", "just exploring"]
SPAM_WORDS = ["backlink", "seo package", "cheap loan", "crypto investment", "follow us", "buy followers", "casino"]
NO_BUDGET_WORDS = ["no budget", "not sure yet", "unknown budget", "tbd"]


def _analyze_with_fallback(lead: dict[str, Any]) -> dict[str, Any]:
    message = (lead.get("message") or "").lower()
    budget = (lead.get("estimated_budget") or "").strip()
    timeline = (lead.get("timeline") or "").lower()
    company = (lead.get("company") or "").strip()

    is_spam = any(w in message for w in SPAM_WORDS) or len(message) < 5

    has_budget = bool(budget) and budget.lower() not in NO_BUDGET_WORDS
    is_urgent = any(w in message for w in URGENT_WORDS) or any(w in timeline for w in URGENT_WORDS)
    is_low_intent = any(w in message for w in LOW_INTENT_WORDS)
    has_clear_ask = any(
        w in message
        for w in ["automat", "need", "looking for", "look into", "help with", "implement", "build", "integrate"]
    )

    if is_spam:
        qualification = QUALIFICATION_UNQUALIFIED
        priority = PRIORITY_LOW
        urgency = "Low"
        intent = "Spam / Irrelevant"
        potential_fit = "Poor fit"
        action = "No immediate action"
        summary = "Message does not describe a genuine business inquiry."
    elif is_urgent and (has_budget or has_clear_ask) and company:
        qualification = QUALIFICATION_HOT
        priority = PRIORITY_HIGH
        urgency = "High"
        intent = "Process Automation" if has_clear_ask else "General Inquiry"
        potential_fit = "Strong fit"
        action = "Call within 1 hour"
        summary = f"{company or 'The lead'} describes an urgent need and is asking for concrete help."
    elif is_low_intent or (not has_clear_ask and not has_budget):
        qualification = QUALIFICATION_LOW_PRIORITY
        priority = PRIORITY_LOW
        urgency = "Low"
        intent = "General Information Request"
        potential_fit = "Unclear fit"
        action = "Send additional information"
        summary = "Inquiry is general in nature, without a specific project or timeline mentioned."
    elif has_clear_ask and (has_budget or company):
        qualification = QUALIFICATION_WARM
        priority = PRIORITY_MEDIUM
        urgency = "Medium"
        intent = "Process Automation" if "automat" in message else "Service Inquiry"
        potential_fit = "Good fit"
        action = "Schedule discovery call"
        summary = f"{company or 'The lead'} shows genuine interest but no immediate urgency."
    else:
        qualification = QUALIFICATION_LOW_PRIORITY
        priority = PRIORITY_MEDIUM
        urgency = "Low"
        intent = "General Inquiry"
        potential_fit = "Unclear fit"
        action = "Manual review"
        summary = "Inquiry does not contain enough information for a confident qualification."

    return {
        "intent": intent,
        "summary": summary,
        "qualification": qualification,
        "priority": priority,
        "potential_fit": potential_fit,
        "urgency": urgency,
        "recommended_action": action,
        "analysis_mode": ANALYSIS_MODE_FALLBACK,
    }
