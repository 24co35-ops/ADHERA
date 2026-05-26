import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch

client = TestClient(app)

def mock_get_current_user():
    return {"user_id": "test-user", "role": "patient"}

@patch("app.routers.analytics.supabase")
def test_get_dashboard_data(mock_supabase):
    # Mock adherence data
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"status": "taken", "scheduled_utc": "2026-05-26T08:00:00Z"},
        {"status": "missed", "scheduled_utc": "2026-05-25T08:00:00Z"}
    ]
    
    # Mock feedback data
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"id": "fb1", "severity": 2, "description": "Nausea", "occurred_at": "2026-05-26T09:00:00Z"}
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    response = client.get("/v1/analytics/dashboard", headers={"Authorization": "Bearer fake-token"})
    
    app.dependency_overrides = {}
        
    assert response.status_code == 200
    data = response.json()
    assert "weekly_adherence" in data
    assert "monthly_adherence" in data
    assert data["weekly_adherence"] == 50.0
    assert len(data["recent_feedback"]) == 1
    assert data["recent_feedback"][0]["description"] == "Nausea"
