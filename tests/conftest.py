"""Test fixtures: every test run gets its own throwaway SQLite file so
tests never touch data/leads.db, and can't leak state between tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_leads.db"
    monkeypatch.setattr(db, "DB_PATH", test_db_path)
    db.init_db()
    yield
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def client(monkeypatch):
    # No key configured for API tests by default -> deterministic fallback mode.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
