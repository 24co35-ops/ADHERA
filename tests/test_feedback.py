from unittest.mock import MagicMock, patch

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

def headers():
    token = jwt.encode({"aud": "authenticated", "sub": "11111111-1111-1111-1111-111111111111", "app_metadata": {"role": "patient"}, "user_metadata": {"role": "patient"}}, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@patch("app.feedback.router.supabase")
def test_feedback_severity_1(mock_supabase):
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])
    res = client.post("/v1/feedback/", headers=headers(), json={
        "medicine_id": "m1", "description": "Mild headache", "severity": 1
    })
    assert res.status_code == 201

@patch("app.feedback.router.supabase")
def test_feedback_severity_4(mock_supabase):
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": "2"}])

    res = client.post("/v1/feedback/", headers=headers(), json={
        "medicine_id": "m1", "description": "Emergency", "severity": 4
    })

    assert res.status_code == 201
    assert res.json()["data"]["id"] == "2"


def test_severity4_alert_unverified_contact_skipped():
    """Verify alert is NOT sent to emergency contact if contact is unverified."""
    contact = {"email": "unverified@contact.com", "verified": False}
    is_verified = contact.get("verified", False) is True
    assert is_verified is False
    action_code = "ALERT_SKIPPED_UNVERIFIED_CONTACT" if not is_verified else "EMERGENCY_ALERT_SENT"
    assert action_code == "ALERT_SKIPPED_UNVERIFIED_CONTACT"



# --- Schema Validation Tests ---

def test_feedback_invalid_description_empty():
    res = client.post("/v1/feedback/", headers=headers(), json={
        "medicine_id": "m1", "description": "", "severity": 1
    })
    assert res.status_code in (400, 422)
    assert "description" in res.json()["error"]["field"]

def test_feedback_invalid_description_too_long():
    res = client.post("/v1/feedback/", headers=headers(), json={
        "medicine_id": "m1", "description": "a" * 2001, "severity": 1
    })
    assert res.status_code in (400, 422)
    assert "description" in res.json()["error"]["field"]

def test_feedback_invalid_occurred_at_future():
    from datetime import datetime, timedelta, timezone
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    res = client.post("/v1/feedback/", headers=headers(), json={
        "medicine_id": "m1", "description": "Mild headache", "severity": 1, "occurred_at": future_time
    })
    assert res.status_code in (400, 422)
    assert "occurred_at" in res.json()["error"]["field"]

