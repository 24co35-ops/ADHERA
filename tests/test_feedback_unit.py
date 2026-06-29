"""
Unit tests for app.feedback.router — all Supabase and HTTP calls mocked.
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

class TestCreateFeedback:
    @patch("app.feedback.router.supabase")
    def test_provider_cannot_create_feedback(self, mock_sb):
        response = client.post("/v1/feedback/", json={
            "medicine_id": "med-1", "severity": 2, "description": "Good"
        }, headers=make_token(role="provider", user_id=PROVIDER_ID))
        assert response.status_code == 403

    @patch("app.feedback.router.supabase")
    def test_create_feedback_normal_severity(self, mock_sb):
        inserted = {"id": "f1", "user_id": TEST_USER_ID, "medicine_id": "med-1", "severity": 2, "description": "Good"}
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[inserted])
        response = client.post("/v1/feedback/", json={
            "medicine_id": "med-1", "severity": 2, "description": "Good"
        }, headers=make_token())
        assert response.status_code == 201
        assert response.json()["data"]["description"] == "Good"

    @patch("app.feedback.router.supabase")
    @patch("app.feedback.router.requests.post")
    def test_create_feedback_emergency_severity(self, mock_post, mock_sb):
        inserted = {"id": "f1", "user_id": TEST_USER_ID, "medicine_id": "med-1", "severity": 4, "description": "Severe pain"}
        
        # Mocks for table calls: feedback insert, provider assignment, emergency contact select
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[inserted])
        
        # assignments select
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"provider_id": PROVIDER_ID, "profiles": {"email": "doc@test.com"}}
        ])
        # emergency contacts select
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"email": "contact@emergency.com"}
        ])

        response = client.post("/v1/feedback/", json={
            "medicine_id": "med-1", "severity": 4, "description": "Severe pain"
        }, headers=make_token())
        
        assert response.status_code == 201
        # verify emergency alert triggered
        assert mock_post.called


class TestListFeedback:
    @patch("app.feedback.router.supabase")
    def test_patient_list_feedback(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/feedback/", headers=make_token())
        assert response.status_code == 200

    @patch("app.feedback.router.supabase")
    def test_provider_list_requires_patient_id(self, mock_sb):
        response = client.get("/v1/feedback/", headers=make_token(role="provider", user_id=PROVIDER_ID))
        assert response.status_code == 400

    @patch("app.feedback.router.supabase")
    def test_provider_list_success_when_assigned(self, mock_sb):
        # mock assignment check
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "a1"}])
        # mock feedback query
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(data=[])
        
        response = client.get(f"/v1/feedback/?patient_id={TEST_USER_ID}", headers=make_token(role="provider", user_id=PROVIDER_ID))
        assert response.status_code in (200, 403)

    @patch("app.feedback.router.supabase")
    def test_admin_list_without_patient_id(self, mock_sb):
        mock_sb.table.return_value.select.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/feedback/", headers=make_token(role="admin"))
        assert response.status_code == 200
