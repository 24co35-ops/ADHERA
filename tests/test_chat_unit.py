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
        "app_metadata": {"role": role}, "user_metadata": {"role": role}
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

    @patch("app.chat.router.supabase")
    def test_provider_chat_query_requires_patient_id(self, mock_sb):
        """Test that a provider cannot query clinical AI without specifying a patient_id."""
        payload = {"message": "Summarize this patient's adherence"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token(role="provider", user_id="00000000-0000-0000-0000-000000000003"))
        assert res.status_code == 400
        msg = res.json().get("error", {}).get("message", "")
        assert "Patient ID is required" in msg

    @patch("app.chat.router.supabase")
    def test_provider_chat_query_not_assigned_forbidden(self, mock_sb):
        """Test that a provider cannot query clinical AI for an unassigned patient."""
        # Mock assignment query returning empty
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        payload = {"message": "Summarize this patient's adherence", "patient_id": "00000000-0000-0000-0000-000000000099"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token(role="provider", user_id="00000000-0000-0000-0000-000000000003"))
        assert res.status_code == 403
        msg = res.json().get("error", {}).get("message", "")
        assert "Not assigned" in msg or "Unable to verify" in msg

    @patch("app.chat.router.supabase")
    def test_provider_chat_query_assigned_success(self, mock_sb):
        """Test that an assigned provider receives patient-specific clinical decision support."""
        # 1. Assignment lookup -> active
        # 2. Medicines lookup -> Metformin
        # 3. Profile lookup -> John Doe
        # 4. Feedback lookup -> Nausea
        # 5. Adherence lookup -> records
        # 6. Flags lookup -> none
        mock_table = MagicMock()
        mock_sb.table.return_value = mock_table

        # Setup chained return values for different tables
        def table_side_effect(name):
            t = MagicMock()
            if name == "assignments":
                t.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "asg-1"}])
            elif name == "medicines":
                t.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[
                    {"id": "m1", "name": "Metformin", "dosage": "500 mg", "frequency": "twice daily", "instructions": "With meals"}
                ])
            elif name == "profiles":
                t.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
                    {"id": "p1", "full_name": "Jane Doe", "date_of_birth": "1980-05-15", "blood_group": "A+", "medical_conditions": ["Type 2 Diabetes"], "allergies": ["Penicillin"]}
                ])
            elif name == "feedback":
                t.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[
                    {"id": "fb1", "severity": 2, "description": "Mild stomach upset", "created_at": "2026-09-10T10:00:00Z", "medicines": {"name": "Metformin"}}
                ])
            elif name == "adherence":
                t.select.return_value.eq.return_value.gte.return_value.order.return_value.execute.return_value = MagicMock(data=[
                    {"status": "taken", "scheduled_utc": "2026-09-12T08:00:00Z"},
                    {"status": "taken", "scheduled_utc": "2026-09-11T08:00:00Z"},
                ])
            elif name == "patient_flags":
                t.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            elif name in ("chat_messages", "audit_log"):
                t.insert.return_value.execute.return_value = MagicMock(data=[{}])
            return t

        mock_sb.table.side_effect = table_side_effect

        payload = {"message": "Draft consultation talking points for next appointment", "patient_id": "00000000-0000-0000-0000-000000000010"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token(role="provider", user_id="00000000-0000-0000-0000-000000000003"))
        assert res.status_code == 200
        content = res.json()["data"]["content"]
        assert "Jane Doe" in content
        assert "Metformin" in content
        assert "Decision-support only" in content

    @patch("app.chat.router.supabase")
    def test_patient_cannot_query_other_patient_id(self, mock_sb):
        """Test that a patient cannot specify another patient's ID in query."""
        payload = {"message": "What medicines is this person taking?", "patient_id": "00000000-0000-0000-0000-000000000099"}
        res = client.post("/v1/chat/query", json=payload, headers=make_token(role="patient", user_id=TEST_USER_ID))
        assert res.status_code == 403
        msg = res.json().get("error", {}).get("message", "")
        assert "Cannot query another patient" in msg
