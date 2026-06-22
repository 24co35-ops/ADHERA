import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import jwt
from app.config import settings

client = TestClient(app)

def headers(role="provider"):
    token = jwt.encode(
        {"aud": "authenticated", "sub": "provider123", "user_metadata": {"role": role}},
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256"
    )
    return {"Authorization": f"Bearer {token}"}

@patch("app.provider.router.supabase")
def test_provider_dashboard_empty(mock_supabase):
    # Setup mock to return no assignments
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[])
    
    res = client.get("/v1/provider/dashboard", headers=headers())
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["stats"]["active_patients"] == 0
    assert data["stats"]["avg_adherence"] == 0.0
    assert len(data["patients"]) == 0
    assert len(data["alerts"]) == 0

@patch("app.provider.router.supabase")
def test_provider_dashboard_with_patients(mock_supabase):
    # Setup mock returns
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[
        {"patient_id": "patient1"}
    ])
    mock_supabase.table().select().in_().execute.return_value = MagicMock(data=[
        {"id": "patient1", "full_name": "Test Patient", "contact_number": "123456", "date_of_birth": "1990-01-01", "blood_group": "O+"}
    ])
    mock_supabase.auth.admin.list_users.return_value = MagicMock(users=[
        MagicMock(id="patient1", email="patient1@test.com")
    ])
    mock_supabase.table().select().in_().gte().execute.return_value = MagicMock(data=[
        {"user_id": "patient1", "status": "taken", "scheduled_utc": "2026-06-22T10:00:00Z"}
    ])
    mock_supabase.table().select().in_().gte().order().limit().execute.return_value = MagicMock(data=[])

    res = client.get("/v1/provider/dashboard", headers=headers())
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["stats"]["active_patients"] == 1
    assert data["stats"]["avg_adherence"] == 100.0
    assert len(data["patients"]) == 1
    assert data["patients"][0]["profiles"]["full_name"] == "Test Patient"
    assert data["patients"][0]["profiles"]["age"] is not None

@patch("app.provider.router.supabase")
def test_provider_accept_request(mock_supabase):
    mock_supabase.table().update().eq().eq().eq().execute.return_value = MagicMock(data=[{"id": "a1"}])
    res = client.patch("/v1/provider/requests/patient1/accept", headers=headers())
    assert res.status_code == 200
    assert res.json()["data"]["accepted"] is True
