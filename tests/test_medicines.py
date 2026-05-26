import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch

client = TestClient(app)

def mock_get_current_user():
    return {"user_id": "test-user", "role": "patient"}

@patch("app.routers.medicines.supabase")
def test_create_medicine(mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "med-id",
            "user_id": "test-user",
            "name": "Aspirin",
            "dosage_amount": 100,
            "dosage_unit": "mg",
            "route": "oral",
            "frequency_type": "daily",
            "start_date": "2026-01-01",
            "is_active": True
        }
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    payload = {
        "name": "Aspirin",
        "dosage_amount": 100,
        "dosage_unit": "mg",
        "route": "oral",
        "frequency_type": "daily",
        "start_date": "2026-06-01"
    }
    
    response = client.post("/v1/medicines/", json=payload)
    app.dependency_overrides = {}
    
    assert response.status_code == 201
    assert response.json()["name"] == "Aspirin"

@patch("app.routers.medicines.supabase")
def test_soft_delete_medicine(mock_supabase):
    # Mock update for soft delete
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "med-id", "is_active": False}
    ]
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    response = client.delete("/v1/medicines/med-id")
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    assert response.json()["message"] == "Medicine deleted"
    
    # Verify the mock was called with is_active: False
    mock_supabase.table.return_value.update.assert_called_with({"is_active": False})
