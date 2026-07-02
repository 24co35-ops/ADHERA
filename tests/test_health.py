"""Tests for GET /v1/health endpoint."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture()
def client():
    """Isolated TestClient; each test gets its own instance."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_supabase_main():
    """Patch the supabase singleton imported directly into app.main."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [{"id": "1"}]
    with patch("app.main.supabase", mock_sb):
        yield mock_sb


def test_health_returns_ok(client, mock_supabase_main):
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


def test_health_no_auth_required(client, mock_supabase_main):
    """Endpoint must be reachable without Authorization header."""
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_db_error(client):
    """When Supabase query raises, db field must be 'error'."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
        "connection refused"
    )
    with patch("app.main.supabase", mock_sb):
        response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ok"
    assert data["db"] == "error"
    # timestamp still present even on DB error
    datetime.fromisoformat(data["timestamp"])


def test_config_endpoint_success(client):
    """Verify GET /v1/config returns config variables and no-cache headers."""
    response = client.get("/v1/config")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "SUPABASE_URL" in data
    assert "SUPABASE_ANON_KEY" in data
    assert "VAPID_PUBLIC_KEY" in data
    assert response.headers["cache-control"] == "no-store, no-cache, must-revalidate, max-age=0"
