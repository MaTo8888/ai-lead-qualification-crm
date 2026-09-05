from app import ai_analysis
from app.constants import (
    ANALYSIS_MODE_AI,
    ANALYSIS_MODE_FALLBACK,
    QUALIFICATION_HOT,
    QUALIFICATION_UNQUALIFIED,
)


def test_no_api_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = ai_analysis.analyze_lead({
        "message": "We urgently need to automate our lead intake, budget is approved.",
        "estimated_budget": "10000 EUR", "timeline": "urgent", "company": "Acme GmbH",
    })
    assert result["analysis_mode"] == ANALYSIS_MODE_FALLBACK
    assert result["qualification"] == QUALIFICATION_HOT


def test_fallback_flags_spam_as_unqualified(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = ai_analysis.analyze_lead({"message": "Buy our cheap SEO package and backlink service now!"})
    assert result["qualification"] == QUALIFICATION_UNQUALIFIED


def test_missing_llm_api_key_never_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = ai_analysis.analyze_lead({"message": ""})
    assert set(ai_analysis.REQUIRED_KEYS).issubset(result.keys())


def test_llm_failure_falls_back_gracefully(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def _raise(*args, **kwargs):
        raise RuntimeError("simulated API outage")

    monkeypatch.setattr(ai_analysis, "_analyze_with_anthropic", _raise)
    result = ai_analysis.analyze_lead({"message": "We need automation help urgently.", "estimated_budget": "5000 EUR"})
    assert result["analysis_mode"] == ANALYSIS_MODE_FALLBACK


def test_invalid_ai_json_falls_back_gracefully(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def _bad_json(*args, **kwargs):
        raise ValueError("AI response missing keys: ['priority']")

    monkeypatch.setattr(ai_analysis, "_analyze_with_anthropic", _bad_json)
    result = ai_analysis.analyze_lead({"message": "We need automation help."})
    assert result["analysis_mode"] == ANALYSIS_MODE_FALLBACK


def test_parse_json_response_strips_markdown_fences():
    parsed = ai_analysis._parse_json_response(
        '```json\n{"intent": "x", "summary": "y", "qualification": "WARM", '
        '"priority": "MEDIUM", "potential_fit": "Good", "urgency": "Medium", '
        '"recommended_action": "Schedule discovery call"}\n```'
    )
    assert parsed["qualification"] == "WARM"


def test_ai_success_path_marks_mode_ai(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    def _fake_success(lead, api_key):
        return {
            "intent": "Process Automation", "summary": "Test summary.", "qualification": "HOT",
            "priority": "HIGH", "potential_fit": "Strong fit", "urgency": "High",
            "recommended_action": "Call within 1 hour", "analysis_mode": ANALYSIS_MODE_AI,
        }

    monkeypatch.setattr(ai_analysis, "_analyze_with_anthropic", _fake_success)
    result = ai_analysis.analyze_lead({"message": "test"})
    assert result["analysis_mode"] == ANALYSIS_MODE_AI
