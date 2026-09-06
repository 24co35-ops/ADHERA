from unittest.mock import MagicMock, patch

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000002"


def make_token(role="patient", user_id=TEST_USER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}


class TestChatRouter:
    @patch("app.chat.router.supabase")
    def test_chat_query_success(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"id": "m1", "name": "Metformin", "dosage_amount": 500, "dosage_unit": "mg"}
        ])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "How should I take my daily medication and what if I miss a dose?"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        data = res.json()["data"]
        assert "content" in data
        assert "sources" in data
        assert "not medical advice" in data["content"].lower()

    @patch("app.chat.router.supabase")
    def test_chat_query_emergency_guardrail(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "I am having severe chest pain and shortness of breath!"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        data = res.json()["data"]
        assert "emergency" in data["content"].lower()
        assert "911" in data["content"] or "112" in data["content"]

    @patch("app.chat.router.supabase")
    def test_chat_query_diagnosis_refusal(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "Diagnose me: do I have diabetes?"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        data = res.json()["data"]
        assert "cannot diagnose" in data["content"].lower() or "not medical advice" in data["content"].lower()

    @patch("app.chat.router.supabase")
    def test_chat_query_dosage_change_refusal(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "Should I double my dosage if I missed yesterday?"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        data = res.json()["data"]
        assert "never adjust" in data["content"].lower() or "not take two doses" in data["content"].lower() or "consult" in data["content"].lower()

    @patch("app.chat.router.supabase")
    def test_chat_query_side_effect_detection(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"id": "med-123", "name": "Metformin", "dosage_amount": 500, "dosage_unit": "mg"}
        ])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "I am experiencing bad nausea and stomach cramps after Metformin"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["suggested_feedback"] is not None
        assert data["suggested_feedback"]["medicine_name"] == "Metformin"
        assert "Nausea" in data["suggested_feedback"]["possible_side_effect"]

    @patch("app.chat.router.supabase")
    def test_chat_history_success(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[
            {"id": "c1", "user_id": TEST_USER_ID, "role": "user", "content": "Hello", "created_at": "2026-09-06T12:00:00Z"},
            {"id": "c2", "user_id": TEST_USER_ID, "role": "assistant", "content": "Hi there", "created_at": "2026-09-06T12:00:01Z"}
        ])

        res = client.get("/v1/chat/history", headers=make_token())
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 2

    def test_chat_ingest_admin_success(self):
        res = client.post("/v1/chat/ingest", headers=make_token(role="admin", user_id=ADMIN_USER_ID))
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["documents_ingested"] >= 1
        assert "refreshed" in data["status"].lower()

    def test_chat_ingest_non_admin_forbidden(self):
        res = client.post("/v1/chat/ingest", headers=make_token(role="patient"))
        assert res.status_code == 403
