"""Seeds the running API with the fictional demo leads from demo_leads.json.

Posts each lead through the real HTTP API (POST /api/leads) — same code
path a real website form or webhook would use — so every qualification,
duplicate flag and CRM record in the portfolio is genuinely produced by
the pipeline, not hand-written.

Usage (server must already be running, e.g. `uvicorn app.main:app`):
    python scripts/seed_demo_leads.py [--base-url http://127.0.0.1:8000]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

DEMO_LEADS_PATH = Path(__file__).resolve().parent.parent / "demo_leads.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    leads = json.loads(DEMO_LEADS_PATH.read_text(encoding="utf-8"))

    print(f"Seeding {len(leads)} demo leads against {args.base_url} ...\n")
    for entry in leads:
        case = entry.pop("_case", "")
        try:
            response = requests.post(f"{args.base_url}/api/leads", json=entry, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(
                f"[{result['lead_id']}] {case}\n"
                f"    status={result['status']}  qualification={result.get('qualification')}  "
                f"priority={result.get('priority')}  duplicate={result.get('duplicate_status')}"
            )
        except requests.RequestException as exc:
            print(f"[FAILED] {case}: {exc}", file=sys.stderr)
        time.sleep(0.1)

    print("\nDone. Open /portfolio/index.html or /api/leads to inspect the results.")


if __name__ == "__main__":
    main()
