import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import jwt
from app.config import settings

client = TestClient(app)

def headers(role="admin"):
    token = jwt.encode({"aud": "authenticated", "sub": "22222222-2222-2222-2222-222222222222", "user_metadata": {"role": role}}, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@patch("app.admin.router.supabase")
def test_reject_provider_valid(mock_supabase):
    mock_supabase.table().update().eq().execute.return_value = MagicMock(data=[{"id": "p1"}])
    res = client.post("/v1/admin/providers/p1/reject", headers=headers())
    assert res.status_code == 200

@patch("app.admin.router.supabase")
def test_create_assignment_duplicate(mock_supabase):
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[])
    mock_supabase.table().insert().execute.side_effect = Exception("duplicate key value violates unique constraint 'one_active_assignment'")
    res = client.post("/v1/admin/assignments", headers=headers(), json={"patient_id": "1", "provider_id": "2"})
    assert res.status_code == 409

def test_admin_route_forbidden_for_patient():
    res = client.get("/v1/admin/assignments", headers=headers("patient"))
    assert res.status_code == 403
