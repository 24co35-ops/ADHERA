from unittest.mock import MagicMock, patch

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


def make_token(role="patient", user_id=TEST_USER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}


class TestWellnessRouter:
    @patch("app.wellness.router.supabase")
    def test_record_wellness_session_success(self, mock_sb):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{
            "id": "w1",
            "user_id": TEST_USER_ID,
            "pattern_name": "Calm (4-7-8)",
            "duration_seconds": 300,
            "completed_at": "2026-09-06T12:00:00Z"
        }])

        payload = {
            "pattern_name": "Calm (4-7-8)",
            "duration_seconds": 300
        }
        res = client.post("/v1/wellness/sessions", json=payload, headers=make_token())
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["pattern_name"] == "Calm (4-7-8)"
        assert data["duration_seconds"] == 300

    def test_record_wellness_session_unauthenticated(self):
        payload = {"pattern_name": "Calm", "duration_seconds": 60}
        res = client.post("/v1/wellness/sessions", json=payload)
        assert res.status_code in (401, 403)

    @patch("app.wellness.router.supabase")
    def test_get_wellness_sessions_success(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[
            {
                "id": "w1",
                "user_id": TEST_USER_ID,
                "pattern_name": "Focus",
                "duration_seconds": 180,
                "completed_at": "2026-09-06T12:00:00Z"
            }
        ])

        res = client.get("/v1/wellness/sessions", headers=make_token())
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 1
        assert data[0]["pattern_name"] == "Focus"

    def test_get_wellness_sessions_unauthenticated(self):
        res = client.get("/v1/wellness/sessions")
        assert res.status_code in (401, 403)
