"""
Unit tests for app.routers.assignments — all Supabase calls mocked.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from jose import jwt
from app.main import app
from app.config import settings

client = TestClient(app)
app.state.limiter.enabled = False

TEST_USER_ID = "00000000-0000-0000-0000-000000000123"
PROVIDER_ID  = "00000000-0000-0000-0000-000000000200"

def make_token(role="patient", user_id=TEST_USER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}

class TestGetMyProviderAssignments:
    @patch("app.routers.assignments.supabase")
    def test_no_assignment(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/assignments/my-provider", headers=make_token())
        assert response.status_code == 200
        assert response.json()["assigned"] is False
        assert response.json()["data"] is None

    @patch("app.routers.assignments.supabase")
    def test_active_assignment_success(self, mock_sb):
        row = {
            "status": "active",
            "provider_id": PROVIDER_ID,
            "patient_id": TEST_USER_ID,
            "profiles": {"id": PROVIDER_ID, "full_name": "Dr. House", "contact_number": "12345"}
        }
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[row])
        mock_sb.auth.admin.get_user_by_id.return_value = MagicMock(user=MagicMock(email="house@md.com"))
        response = client.get("/v1/assignments/my-provider", headers=make_token())
        assert response.status_code == 200
        assert response.json()["assigned"] is True
        assert response.json()["data"]["profiles"]["email"] == "house@md.com"

    @patch("app.routers.assignments.supabase")
    def test_active_assignment_exception_handled(self, mock_sb):
        row = {
            "status": "active",
            "provider_id": PROVIDER_ID,
            "patient_id": TEST_USER_ID,
            "profiles": {"id": PROVIDER_ID, "full_name": "Dr. House", "contact_number": "12345"}
        }
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[row])
        mock_sb.auth.admin.get_user_by_id.side_effect = Exception("Auth fetch error")
        response = client.get("/v1/assignments/my-provider", headers=make_token())
        assert response.status_code == 200
        assert response.json()["assigned"] is True
        assert response.json()["data"]["profiles"]["email"] == ""


class TestSearchProvidersAssignments:
    @patch("app.routers.assignments.supabase")
    def test_search_no_query(self, mock_sb):
        providers = [{"id": PROVIDER_ID, "full_name": "Dr. House", "contact_number": "123"}]
        q = mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value
        q.limit.return_value.execute.return_value = MagicMock(data=providers)
        mock_sb.auth.admin.list_users.return_value = []
        response = client.get("/v1/assignments/search-providers", headers=make_token())
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    @patch("app.routers.assignments.supabase")
    def test_search_with_query(self, mock_sb):
        providers = [{"id": PROVIDER_ID, "full_name": "Dr. House", "contact_number": "123"}]
        q = mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value
        q.ilike.return_value.limit.return_value.execute.return_value = MagicMock(data=providers)
        mock_sb.auth.admin.list_users.return_value = [MagicMock(id=PROVIDER_ID, email="house@md.com")]
        response = client.get("/v1/assignments/search-providers?query=House", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"][0]["email"] == "house@md.com"


class TestRequestProviderAssignments:
    @patch("app.routers.assignments.supabase")
    def test_missing_provider_id_returns_400(self, mock_sb):
        response = client.post("/v1/assignments/request", json={}, headers=make_token())
        assert response.status_code == 400

    @patch("app.routers.assignments.supabase")
    def test_already_assigned_returns_409(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "a1"}])
        response = client.post("/v1/assignments/request", json={"provider_id": PROVIDER_ID}, headers=make_token())
        assert response.status_code == 409

    @patch("app.routers.assignments.supabase")
    def test_already_pending_returns_409(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[]), # Active check
            MagicMock(data=[{"id": "a2"}]) # Pending check
        ]
        response = client.post("/v1/assignments/request", json={"provider_id": PROVIDER_ID}, headers=make_token())
        assert response.status_code == 409

    @patch("app.routers.assignments.supabase")
    def test_new_request_succeeds(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[]), # Active check
            MagicMock(data=[])  # Pending check
        ]
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])
        response = client.post("/v1/assignments/request", json={"provider_id": PROVIDER_ID}, headers=make_token())
        assert response.status_code == 200
        assert "Request sent" in response.json()["message"]


class TestCancelRequestAssignments:
    @patch("app.routers.assignments.supabase")
    def test_cancel_request_succeeds(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        response = client.delete("/v1/assignments/request", headers=make_token())
        assert response.status_code == 200
        assert response.json()["message"] == "Request cancelled"
