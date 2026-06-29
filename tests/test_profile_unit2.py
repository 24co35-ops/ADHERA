"""
Unit tests for app.profile.router — all Supabase calls mocked.
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

def make_token(role="patient", user_id=TEST_USER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}

class TestGetProfile:
    @patch("app.profile.router.supabase")
    def test_get_profile_success(self, mock_sb):
        profile = {"id": TEST_USER_ID, "full_name": "Alice", "date_of_birth": "1990-01-01"}
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[profile])
        mock_sb.auth.admin.get_user_by_id.return_value = MagicMock(user=MagicMock(email="alice@test.com"))
        
        response = client.get("/v1/profile/", headers=make_token())
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["full_name"] == "Alice"
        assert data["email"] == "alice@test.com"

    @patch("app.profile.router.supabase")
    def test_get_profile_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/profile/", headers=make_token())
        assert response.status_code == 404


class TestUpdateProfile:
    @patch("app.profile.router.supabase")
    def test_update_profile_success(self, mock_sb):
        profile = {"id": TEST_USER_ID, "full_name": "Bob", "date_of_birth": "1990-01-01"}
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[profile])
        
        response = client.patch("/v1/profile/", json={"full_name": "Bob"}, headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["full_name"] == "Bob"

    @patch("app.profile.router.supabase")
    def test_update_profile_empty_returns_400(self, mock_sb):
        response = client.patch("/v1/profile/", json={}, headers=make_token())
        assert response.status_code == 400


class TestEmergencyContact:
    @patch("app.profile.router.supabase")
    def test_get_emergency_contact_empty(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/profile/emergency-contact", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"] == {}

    @patch("app.profile.router.supabase")
    def test_update_emergency_contact(self, mock_sb):
        contact = {"full_name": "Contact Name", "contact_number": "12345", "email": "c@test.com", "relationship": "friend"}
        mock_sb.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[contact])
        response = client.put("/v1/profile/emergency-contact", json=contact, headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["full_name"] == "Contact Name"

    @patch("app.profile.router.supabase")
    def test_delete_emergency_contact(self, mock_sb):
        mock_sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        response = client.delete("/v1/profile/emergency-contact", headers=make_token())
        assert response.status_code == 200


class TestPushSubscription:
    @patch("app.profile.router.supabase")
    def test_save_push_subscription_invalid(self, mock_sb):
        response = client.post("/v1/profile/push-subscription", json={}, headers=make_token())
        assert response.status_code == 400

    @patch("app.profile.router.supabase")
    def test_delete_push_subscription(self, mock_sb):
        mock_sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        response = client.delete("/v1/profile/push-subscription", headers=make_token())
        assert response.status_code == 200

    def test_get_vapid_public_key(self):
        response = client.get("/v1/profile/vapid-public-key", headers=make_token())
        assert response.status_code == 200
        assert "public_key" in response.json()["data"]


class TestExportDataProfile:
    @patch("app.profile.router.supabase")
    def test_export_json(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        response = client.get("/v1/profile/export?format=json", headers=make_token())
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    @patch("app.profile.router.supabase")
    def test_export_csv(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        response = client.get("/v1/profile/export?format=csv", headers=make_token())
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
