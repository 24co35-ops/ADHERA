import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import MagicMock, patch

client = TestClient(app)

@patch("app.db.supabase.supabase")
def test_get_dashboard_data(mock_supabase):
    # Mock data
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"status": "taken"}, {"status": "missed"}
    ]
    
    # Need to mock the auth dependency
    with patch("app.auth.dependencies.get_current_user", return_value={"user_id": "test-user", "role": "patient"}):
        response = client.get("/v1/analytics/dashboard", headers={"Authorization": "Bearer fake-token"})
        
    assert response.status_code == 200
    data = response.json()
    assert data["adherence_rate"] == 50.0
    assert data["total_doses"] == 2
