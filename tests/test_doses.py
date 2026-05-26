import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch

client = TestClient(app)

def mock_get_current_user():
    return {"user_id": "test-user", "role": "patient"}

@patch("app.routers.doses.supabase")
def test_update_dose_status_taken(mock_supabase):
    # Mock dose fetch
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "dose-id", "user_id": "test-user", "snooze_count": 0}
    ]
    # Mock update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {"status": "taken"}
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    response = client.post("/v1/doses/dose-id/status", json={"status": "taken", "scheduled_utc": "2026-05-26T08:00:00Z"})
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    assert response.json()["final_status"] == "taken"

@patch("app.routers.doses.supabase")
def test_update_dose_status_snooze(mock_supabase):
    # Mock dose fetch
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "dose-id", "user_id": "test-user", "snooze_count": 1}
    ]
    # Mock update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {"status": "snoozed", "snooze_count": 2}
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    response = client.post("/v1/doses/dose-id/status", json={"status": "snoozed", "scheduled_utc": "2026-05-26T08:00:00Z"})
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    assert response.json()["status"] == "snoozed"
    assert response.json()["count"] == 2

@patch("app.routers.doses.supabase")
def test_update_dose_status_max_snooze(mock_supabase):
    # Mock dose fetch with 3 snoozes
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "dose-id", "user_id": "test-user", "snooze_count": 3}
    ]
    # Mock update to missed
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {"status": "missed"}
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    response = client.post("/v1/doses/dose-id/status", json={"status": "snoozed", "scheduled_utc": "2026-05-26T08:00:00Z"})
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    assert response.json()["final_status"] == "missed"
