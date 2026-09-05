"""FastAPI application: the lead intake API, plus static hosting for the
live demo form and the portfolio dashboard — all served from one process
so the portfolio's CRM/Pipeline views can fetch real data with no CORS
setup required.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

load_dotenv()

from app import db  # noqa: E402 - loaded after dotenv on purpose
from app.constants import QUALIFICATIONS
from app.models import LeadCreate, LeadOut
from app.pipeline import process_lead

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="AI Lead Qualification & CRM Automation", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return RedirectResponse(url="/portfolio/index.html")


@app.post("/api/leads", response_model=LeadOut)
def create_lead(lead: LeadCreate):
    result = process_lead(lead.model_dump())
    return result


@app.get("/api/leads", response_model=list[LeadOut])
def get_leads(qualification: Optional[str] = None):
    if qualification and qualification not in QUALIFICATIONS:
        raise HTTPException(status_code=400, detail=f"Unknown qualification filter: {qualification}")
    return db.list_leads(qualification=qualification)


@app.get("/api/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str):
    lead = db.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/api/handoffs")
def get_handoffs():
    return db.list_handoffs()


@app.get("/api/stats")
def get_stats():
    leads = db.list_leads()
    by_status: dict[str, int] = {}
    by_qualification: dict[str, int] = {}
    for lead in leads:
        by_status[lead["status"]] = by_status.get(lead["status"], 0) + 1
        if lead.get("qualification"):
            by_qualification[lead["qualification"]] = by_qualification.get(lead["qualification"], 0) + 1
    return {"total_leads": len(leads), "by_status": by_status, "by_qualification": by_qualification}


app.mount("/public", StaticFiles(directory=str(BASE_DIR / "public")), name="public")
app.mount("/portfolio", StaticFiles(directory=str(BASE_DIR / "portfolio")), name="portfolio")
