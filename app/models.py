"""Pydantic schemas for the lead API.

LeadCreate intentionally keeps every field optional at the schema level —
business-rule validation (required fields, email format, empty messages)
happens explicitly in validation.py so the pipeline can return a structured
VALIDATION_FAILED result instead of a raw HTTP 422.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class LeadCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "website_form"
    estimated_budget: Optional[str] = None
    timeline: Optional[str] = None


class LeadOut(BaseModel):
    lead_id: str
    created_at: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    estimated_budget: Optional[str] = None
    timeline: Optional[str] = None
    status: str

    qualification: Optional[str] = None
    priority: Optional[str] = None
    ai_summary: Optional[str] = None
    intent: Optional[str] = None
    potential_fit: Optional[str] = None
    urgency: Optional[str] = None
    duplicate_status: Optional[str] = None
    duplicate_of: Optional[str] = None
    recommended_action: Optional[str] = None
    analysis_mode: Optional[str] = None
    validation_errors: Optional[list[str]] = None
    processed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
