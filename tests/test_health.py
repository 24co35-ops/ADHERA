"""Tests for GET /v1/health endpoint."""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    """Happy path: DB reachable, returns status ok with ISO8601 timestamp."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    # timestamp must be a valid ISO8601 datetime string
    ts = datetime.fromisoformat(data["timestamp"])
    assert ts.tzinfo is not None  # timezone-aware


def test_health_no_auth_required():
    """Endpoint must be reachable without Authorization header."""
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_db_error():
    """When Supabase query raises, db field must be 'error'."""
    with patch("app.main.supabase") as mock_sb:
        mock_sb.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "connection refused"
        )
        response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ok"
    assert data["db"] == "error"
    # timestamp still present even on DB error
    datetime.fromisoformat(data["timestamp"])
