import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch

client = TestClient(app)

def mock_get_current_user():
    return {"user_id": "test-user", "role": "patient"}

@patch("app.routers.feedback.supabase")
def test_create_feedback_normal(mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "fb-id", "severity": 1}
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    payload = {
        "medicine_id": "med-id",
        "description": "Mild headache",
        "severity": 1,
        "occurred_at": "2026-05-26T10:00:00Z"
    }
    
    response = client.post("/v1/feedback/", json=payload)
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    assert response.json()["id"] == "fb-id"

@patch("app.routers.feedback.supabase")
def test_create_feedback_emergency(mock_supabase):
    def mock_table(table_name):
        mock = MagicMock()
        if table_name == "feedback":
            mock.insert.return_value.execute.return_value.data = [{"id": "emergency-fb-id", "severity": 4}]
        elif table_name == "assignments":
            mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{"provider_id": "provider-id"}]
        elif table_name == "profiles":
            mock.select.return_value.eq.return_value.execute.return_value.data = [{"email": "provider@adhera.app"}]
        elif table_name == "emergency_contacts":
            mock.select.return_value.eq.return_value.execute.return_value.data = [{"email": "contact@emergency.com"}]
        return mock

    mock_supabase.table.side_effect = mock_table
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    payload = {
        "medicine_id": "med-id",
        "description": "Severe chest pain",
        "severity": 4,
        "occurred_at": "2026-05-26T10:00:00Z"
    }
    
    with patch("builtins.print") as mock_print:
        response = client.post("/v1/feedback/", json=payload)
        
        mock_print.assert_any_call("Alerting Provider: provider@adhera.app")
        mock_print.assert_any_call("Alerting Emergency Contact: contact@emergency.com")

    app.dependency_overrides = {}
    assert response.status_code == 200
    assert response.json()["severity"] == 4
