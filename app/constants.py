"""Shared status/category constants used across the pipeline."""

# Overall lead status
STATUS_PROCESSING = "PROCESSING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_MANUAL_REVIEW = "MANUAL_REVIEW"
STATUS_VALIDATION_FAILED = "VALIDATION_FAILED"

# Duplicate check outcome
DUPLICATE_NEW = "NEW"
DUPLICATE_POSSIBLE = "POSSIBLE_DUPLICATE"
DUPLICATE_EXISTING = "EXISTING_LEAD"

# Qualification categories
QUALIFICATION_HOT = "HOT"
QUALIFICATION_WARM = "WARM"
QUALIFICATION_LOW_PRIORITY = "LOW_PRIORITY"
QUALIFICATION_UNQUALIFIED = "UNQUALIFIED"
QUALIFICATIONS = [
    QUALIFICATION_HOT,
    QUALIFICATION_WARM,
    QUALIFICATION_LOW_PRIORITY,
    QUALIFICATION_UNQUALIFIED,
]

# Priority levels
PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"
PRIORITIES = [PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]

# AI analysis source — kept on every processed lead so the portfolio/CRM
# can honestly show whether a real LLM or the deterministic fallback produced it.
ANALYSIS_MODE_AI = "ai"
ANALYSIS_MODE_FALLBACK = "fallback_rules"

# Sales handoff delivery channel — no real email/Slack integration is wired
# up in this demo, so handoffs only ever land in the internal queue.
HANDOFF_CHANNEL_INTERNAL_QUEUE = "internal_queue"
