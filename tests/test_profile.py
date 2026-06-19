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
