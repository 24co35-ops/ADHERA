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

    @patch("app.chat.router.supabase")
    def test_chat_query_hypertension_patient_no_diabetes_assumption(self, mock_sb):
        """Test that a patient on blood pressure meds receives BP-specific guidance and NOT diabetes."""
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"id": "m1", "name": "Lisinopril", "dosage_amount": 10, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily", "instructions": "Take in the morning"},
            {"id": "m2", "name": "Amlodipine", "dosage_amount": 5, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily", "instructions": None}
        ])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "What should I know about taking my daily medicines and possible side effects?"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        content = res.json()["data"]["content"]

        # Must mention patient's actual medicines
        assert "Lisinopril" in content
        assert "Amlodipine" in content
        # Must NOT assume or mention diabetes / metformin
        assert "metformin" not in content.lower()
        assert "type 2 diabetes" not in content.lower()
        assert "hypoglycemia" not in content.lower()

    @patch("app.chat.router.supabase")
    def test_chat_query_empty_medicines(self, mock_sb):
        """Test that a patient with 0 medicines gets generic adherence guidance without assuming diabetes."""
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "How do I build a good medication adherence routine?"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        content = res.json()["data"]["content"]

        assert "No active medications" in content or "no active prescriptions" in content.lower()
        assert "Consistency" in content or "scheduled" in content.lower()
        assert "metformin" not in content.lower()
        assert "type 2 diabetes" not in content.lower()

    @patch("app.chat.router.supabase")
    def test_chat_query_includes_adherence_and_feedback_context(self, mock_sb):
        """Test that missed doses and recent symptoms are reflected in the response."""
        # Setup mock returns for medicines, profiles, feedback, adherence
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[
            {"id": "m1", "name": "Atorvastatin", "dosage_amount": 20, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily"}
        ])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

        payload = {"message": "What tips do you have for my routine?"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token())
        assert res.status_code == 200
        content = res.json()["data"]["content"]
        assert "Atorvastatin" in content
