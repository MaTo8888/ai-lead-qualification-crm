"""Sales handoff: for HOT/WARM leads, writes a real record into the
internal notification queue table.

No email/Slack integration is wired up in this demo — the queue itself is
real and queryable (via /api/handoffs and the CRM view), but nothing is
claimed to have actually been emailed or posted to Slack.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app import db
from app.constants import HANDOFF_CHANNEL_INTERNAL_QUEUE, QUALIFICATION_HOT, QUALIFICATION_WARM


def create_handoff_if_needed(lead: dict[str, Any]) -> Optional[dict[str, Any]]:
    if lead.get("qualification") not in (QUALIFICATION_HOT, QUALIFICATION_WARM):
        return None

    handoff = {
        "handoff_id": "HANDOFF-" + uuid.uuid4().hex[:8],
        "lead_id": lead["lead_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "company": lead.get("company") or "",
        "contact_name": f"{lead.get('first_name') or ''} {lead.get('last_name') or ''}".strip(),
        "qualification": lead.get("qualification") or "",
        "priority": lead.get("priority") or "",
        "summary": lead.get("ai_summary") or "",
        "recommended_action": lead.get("recommended_action") or "",
        "channel": HANDOFF_CHANNEL_INTERNAL_QUEUE,
        "delivery_status": "QUEUED",
    }
    db.insert_handoff(handoff)
    return handoff
