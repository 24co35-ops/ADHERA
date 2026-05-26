import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch

client = TestClient(app)

def mock_get_current_user():
    return {"user_id": "test-user", "role": "patient"}

@patch("app.routers.reminders.supabase")
def test_create_reminder_with_conflict(mock_supabase):
    # Mock existing reminders to trigger conflict
    # One reminder at 08:15:00
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"dose_time_utc": "08:15:00"}
    ]
    
    # Mock insertion
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "new-reminder-id",
            "medicine_id": "med-id",
            "user_id": "test-user",
            "dose_label": "morning",
            "dose_time_utc": "08:00:00",
            "timezone": "UTC",
            "recurrence_type": "daily",
            "is_active": True
        }
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    payload = {
        "medicine_id": "med-id",
        "dose_label": "morning",
        "dose_time_utc": "08:00:00",
        "timezone": "UTC",
        "recurrence_type": "daily"
    }
    
    response = client.post("/v1/reminders/", json=payload)
    
    app.dependency_overrides = {}
    
    assert response.status_code == 201
    data = response.json()
    assert "warning" in data
    assert "Conflict detected" in data["warning"]
    assert data["dose_time_utc"] == "08:00:00"

@patch("app.routers.reminders.supabase")
def test_create_reminder_no_conflict(mock_supabase):
    # Mock no existing reminders
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    
    # Mock insertion
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "new-reminder-id",
            "medicine_id": "med-id",
            "user_id": "test-user",
            "dose_label": "afternoon",
            "dose_time_utc": "14:00:00",
            "timezone": "UTC",
            "recurrence_type": "daily",
            "is_active": True
        }
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    payload = {
        "medicine_id": "med-id",
        "dose_label": "afternoon",
        "dose_time_utc": "14:00:00",
        "timezone": "UTC",
        "recurrence_type": "daily"
    }
    
    response = client.post("/v1/reminders/", json=payload)
    
    app.dependency_overrides = {}
    
    assert response.status_code == 201
    data = response.json()
    assert "warning" not in data or data["warning"] is None
