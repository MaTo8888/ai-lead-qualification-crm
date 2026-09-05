"""Orchestrates the full lead pipeline:

New Lead -> Validation -> Duplicate Check -> AI Analysis -> Qualification
         -> CRM -> Sales Handoff

Every step is logged. A failure anywhere after validation is caught and
turned into a MANUAL_REVIEW record rather than crashing the request —
the lead is never silently lost.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app import ai_analysis, db, duplicate_check, handoff, qualification, validation
from app.constants import (
    STATUS_COMPLETED,
    STATUS_MANUAL_REVIEW,
    STATUS_VALIDATION_FAILED,
)
from app.logging_setup import configure_logging

log = configure_logging()


def process_lead(raw_input: dict[str, Any]) -> dict[str, Any]:
    lead_id = "LEAD-" + uuid.uuid4().hex[:8]
    created_at = datetime.now(timezone.utc).isoformat()
    log.info("Lead received (lead_id=%s, source=%s)", lead_id, raw_input.get("source"))

    is_valid, errors, normalized = validation.validate_lead(raw_input)

    lead: dict[str, Any] = {
        "lead_id": lead_id,
        "created_at": created_at,
        **normalized,
    }

    if not is_valid:
        lead["status"] = STATUS_VALIDATION_FAILED
        lead["validation_errors"] = errors
        lead["processed_at"] = datetime.now(timezone.utc).isoformat()
        db.insert_lead(lead)
        log.info("Validation failed (lead_id=%s): %s", lead_id, "; ".join(errors))
        return lead

    log.info("Validation passed (lead_id=%s)", lead_id)

    try:
        duplicate_status, duplicate_of = duplicate_check.check_duplicate(
            normalized.get("email", ""), normalized.get("phone", "")
        )
        lead["duplicate_status"] = duplicate_status
        lead["duplicate_of"] = duplicate_of
        log.info("Duplicate check completed (lead_id=%s, result=%s)", lead_id, duplicate_status)

        ai_result = ai_analysis.analyze_lead(normalized)
        signals = qualification.deterministic_signals(normalized)
        final = qualification.combine_qualification(ai_result, signals)
        lead.update({
            "intent": final.get("intent"),
            "ai_summary": final.get("summary"),
            "qualification": final.get("qualification"),
            "priority": final.get("priority"),
            "potential_fit": final.get("potential_fit"),
            "urgency": final.get("urgency"),
            "recommended_action": final.get("recommended_action"),
            "analysis_mode": final.get("analysis_mode"),
        })
        log.info(
            "AI analysis completed (lead_id=%s, mode=%s, qualification=%s)",
            lead_id, lead["analysis_mode"], lead["qualification"],
        )

        lead["status"] = STATUS_COMPLETED
        lead["processed_at"] = datetime.now(timezone.utc).isoformat()
        db.insert_lead(lead)
        log.info("CRM updated (lead_id=%s, status=%s)", lead_id, lead["status"])

        created_handoff = handoff.create_handoff_if_needed(lead)
        if created_handoff:
            log.info(
                "Handoff generated (lead_id=%s, handoff_id=%s, channel=%s)",
                lead_id, created_handoff["handoff_id"], created_handoff["channel"],
            )

        return lead

    except Exception as exc:  # noqa: BLE001 - any unexpected failure becomes MANUAL_REVIEW, never a crash
        log.error("Pipeline error (lead_id=%s): %s: %s", lead_id, type(exc).__name__, exc)
        lead["status"] = STATUS_MANUAL_REVIEW
        lead["validation_errors"] = [f"Automated processing failed: {type(exc).__name__}"]
        lead["processed_at"] = datetime.now(timezone.utc).isoformat()
        db.insert_lead(lead)
        return lead
