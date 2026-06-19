import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
import jwt
from app.config import settings

client = TestClient(app)

def get_token(role="patient"):
    return jwt.encode({"aud": "authenticated", "sub": "user-uuid-123", "user_metadata": {"role": role}}, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

def headers(role="patient"):
    return {"Authorization": f"Bearer {get_token(role)}"}

@patch("app.profile.router.supabase")
def test_save_push_subscription_valid(mock_supabase):
    mock_supabase.table().upsert().execute.return_value = type('obj', (object,), {'data': [{'id': '1'}]})()
    
    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/some-token",
        "keys": {
            "auth": "auth_secret_key",
            "p256dh": "p256dh_public_key"
        }
    }
    res = client.post("/v1/profile/push-subscription", headers=headers(), json=payload)
    assert res.status_code == 200
    assert res.json()["data"]["id"] == "1"

def test_save_push_subscription_missing_keys():
    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/some-token",
        "keys": {
            "auth": "auth_secret_key"
        }
    }
    res = client.post("/v1/profile/push-subscription", headers=headers(), json=payload)
    assert res.status_code == 400

# --- Export Tests ---

@patch("app.profile.router.supabase")
def test_export_json(mock_supabase):
    mock_supabase.table().select().eq().order().execute.return_value = type('R', (), {'data': []})()
    mock_supabase.table().select().eq().execute.return_value = type('R', (), {'data': []})()
    mock_supabase.storage.from_().upload.return_value = {}
    mock_supabase.storage.from_().create_signed_url.return_value = {"signedURL": "https://example.com/export.json?token=abc"}

    res = client.get("/v1/profile/export?format=json", headers=headers())
    assert res.status_code == 200
    data = res.json()["data"]
    assert "signed_url" in data
    assert data["format"] == "json"
    assert data["expires_in"] == 900

@patch("app.profile.router.supabase")
def test_export_csv(mock_supabase):
    adherence_row = {
        "scheduled_utc": "2025-01-15T08:00:00Z",
        "status": "taken",
        "notes": "Feeling good",
        "reminders": {"dose_label": "morning", "medicines": {"name": "Aspirin"}}
    }
    mock_supabase.table().select().eq().order().execute.return_value = type('R', (), {'data': [adherence_row]})()
    mock_supabase.table().select().eq().execute.return_value = type('R', (), {'data': []})()
    mock_supabase.storage.from_().upload.return_value = {}
    mock_supabase.storage.from_().create_signed_url.return_value = {"signedURL": "https://example.com/export.csv?token=abc"}

    res = client.get("/v1/profile/export?format=csv", headers=headers())
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["format"] == "csv"
    assert "signed_url" in data

def test_export_invalid_format():
    res = client.get("/v1/profile/export?format=xml", headers=headers())
    assert res.status_code in (400, 422)
