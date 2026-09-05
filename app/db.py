"""SQLite persistence for leads and sales handoffs.

Deliberately plain sqlite3 (no ORM) — the schema is small and stable enough
that an ORM would only add indirection without real benefit here.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "leads.db"

LEAD_COLUMNS = [
    "lead_id", "created_at", "first_name", "last_name", "company", "email",
    "phone", "website", "company_size", "industry", "message", "source",
    "estimated_budget", "timeline", "status",
    "qualification", "priority", "ai_summary", "intent", "potential_fit",
    "urgency", "duplicate_status", "duplicate_of", "recommended_action",
    "analysis_mode", "validation_errors", "processed_at",
]

HANDOFF_COLUMNS = [
    "handoff_id", "lead_id", "created_at", "company", "contact_name",
    "qualification", "priority", "summary", "recommended_action",
    "channel", "delivery_status",
]


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS leads (
                {", ".join(c + " TEXT" for c in LEAD_COLUMNS)},
                PRIMARY KEY (lead_id)
            )
        """)
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS handoffs (
                {", ".join(c + " TEXT" for c in HANDOFF_COLUMNS)},
                PRIMARY KEY (handoff_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone)")
        conn.commit()
    finally:
        conn.close()


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    if isinstance(row.get("validation_errors"), list):
        row["validation_errors"] = json.dumps(row["validation_errors"])
    return row


def _deserialize(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    if data.get("validation_errors"):
        try:
            data["validation_errors"] = json.loads(data["validation_errors"])
        except (TypeError, json.JSONDecodeError):
            data["validation_errors"] = None
    return data


def insert_lead(lead: dict[str, Any]) -> None:
    row = _serialize(lead)
    columns = [c for c in LEAD_COLUMNS if c in row]
    placeholders = ", ".join("?" for _ in columns)
    conn = get_connection()
    try:
        conn.execute(
            f"INSERT INTO leads ({', '.join(columns)}) VALUES ({placeholders})",
            [row[c] for c in columns],
        )
        conn.commit()
    finally:
        conn.close()


def update_lead(lead_id: str, fields: dict[str, Any]) -> None:
    row = _serialize(fields)
    columns = [c for c in LEAD_COLUMNS if c in row]
    if not columns:
        return
    set_clause = ", ".join(f"{c} = ?" for c in columns)
    conn = get_connection()
    try:
        conn.execute(
            f"UPDATE leads SET {set_clause} WHERE lead_id = ?",
            [row[c] for c in columns] + [lead_id],
        )
        conn.commit()
    finally:
        conn.close()


def get_lead(lead_id: str) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM leads WHERE lead_id = ?", [lead_id]).fetchone()
        return _deserialize(row) if row else None
    finally:
        conn.close()


def find_by_email(email: str) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM leads WHERE lower(email) = lower(?) ORDER BY created_at DESC",
            [email],
        ).fetchall()
        return [_deserialize(r) for r in rows]
    finally:
        conn.close()


def find_by_phone(phone_digits: str) -> list[dict[str, Any]]:
    if not phone_digits:
        return []
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM leads").fetchall()
        out = []
        for r in rows:
            existing_digits = "".join(ch for ch in (r["phone"] or "") if ch.isdigit())
            if existing_digits and existing_digits == phone_digits:
                out.append(_deserialize(r))
        return out
    finally:
        conn.close()


def list_leads(qualification: Optional[str] = None) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        if qualification:
            rows = conn.execute(
                "SELECT * FROM leads WHERE qualification = ? ORDER BY created_at DESC",
                [qualification],
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
        return [_deserialize(r) for r in rows]
    finally:
        conn.close()


def insert_handoff(handoff: dict[str, Any]) -> None:
    columns = [c for c in HANDOFF_COLUMNS if c in handoff]
    placeholders = ", ".join("?" for _ in columns)
    conn = get_connection()
    try:
        conn.execute(
            f"INSERT INTO handoffs ({', '.join(columns)}) VALUES ({placeholders})",
            [handoff[c] for c in columns],
        )
        conn.commit()
    finally:
        conn.close()


def list_handoffs() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM handoffs ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def reset_db() -> None:
    """Drops and recreates all tables. Used by tests and the seed script."""
    conn = get_connection()
    try:
        conn.execute("DROP TABLE IF EXISTS leads")
        conn.execute("DROP TABLE IF EXISTS handoffs")
        conn.commit()
    finally:
        conn.close()
    init_db()
