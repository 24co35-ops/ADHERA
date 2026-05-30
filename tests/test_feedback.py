import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import jwt
from app.config import settings

client = TestClient(app)

def headers():
    token = jwt.encode({"aud": "authenticated", "sub": "user123", "user_metadata": {"role": "patient"}}, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@patch("app.feedback.router.supabase")
def test_feedback_severity_1(mock_supabase):
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])
    res = client.post("/v1/feedback/", headers=headers(), json={
        "medicine_id": "m1", "description": "Mild headache", "severity": 1
    })
    assert res.status_code == 201

@patch("app.feedback.router.requests.post")
@patch("app.feedback.router.supabase")
def test_feedback_severity_4(mock_supabase, mock_requests_post):
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": "2"}])
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[{"profiles": {"email": "p@demo.com"}}])
    
    res = client.post("/v1/feedback/", headers=headers(), json={
        "medicine_id": "m1", "description": "Emergency", "severity": 4
    })
    
    assert res.status_code == 201
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    assert "/functions/v1/emergency-alert" in args[0]
