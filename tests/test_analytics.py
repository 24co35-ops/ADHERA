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

@patch("app.analytics.router.supabase")
def test_adherence_rate(mock_supabase):
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[
        {"status": "taken"}, {"status": "taken"}, {"status": "missed"}
    ])
    res = client.get("/v1/analytics/adherence", headers=headers())
    assert res.status_code == 200
    assert res.json()["data"]["rate"] == 66.7

@patch("app.analytics.router.supabase")
def test_dashboard_warning(mock_supabase):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[
        {"status": "taken", "scheduled_utc": now},
        {"status": "missed", "scheduled_utc": now},
        {"status": "missed", "scheduled_utc": now}
    ])
    res = client.get("/v1/analytics/dashboard", headers=headers())
    assert res.status_code == 200
    assert res.json()["data"]["weekly_warning"] == True
