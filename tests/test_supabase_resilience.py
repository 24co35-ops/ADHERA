"""
Unit tests verifying database resilience, Gateway Timeout (504) handling,
and active prescription preservation under partial database failures.
"""
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from jose import jwt
from postgrest.exceptions import APIError

from app.config import settings
from app.main import app

client = TestClient(app)
app.state.limiter.enabled = False

TEST_PROVIDER_ID = "00000000-0000-0000-0000-000000000200"
TEST_PATIENT_ID = "00000000-0000-0000-0000-000000000123"


def make_token(role="provider", user_id=TEST_PROVIDER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "app_metadata": {"role": role}, "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}


class TestDatabaseTimeoutHandling:
    @patch("app.analytics.router.supabase")
    def test_analytics_adherence_timeout_returns_504(self, mock_sb):
        # Simulate PostgREST 504 gateway timeout
        mock_sb.table.side_effect = httpx.ReadTimeout("The read operation timed out")
        response = client.get(
            f"/v1/analytics/adherence?patient_id={TEST_PATIENT_ID}",
            headers=make_token(role="patient", user_id=TEST_PATIENT_ID)
        )
        assert response.status_code == 504
        data = response.json()
        assert data["error"]["code"] == "GATEWAY_TIMEOUT"
        assert "timed out" in data["error"]["message"].lower()

    @patch("app.provider.router.supabase")
    def test_provider_patient_profile_timeout_returns_504(self, mock_sb):
        # Assignment check passes, but profiles query times out
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "a1"}]
        )
        # Second call (profiles) raises APIError with Gateway Timeout
        mock_table.select.return_value.eq.return_value.execute.side_effect = APIError(
            {"message": "Gateway Timeout", "code": "504"}
        )
        mock_sb.table.return_value = mock_table

        response = client.get(
            f"/v1/provider/patients/{TEST_PATIENT_ID}",
            headers=make_token(role="provider", user_id=TEST_PROVIDER_ID)
        )
        assert response.status_code == 504
        assert response.json()["error"]["code"] == "GATEWAY_TIMEOUT"


class TestMedicinesResilience:
    @patch("app.medicines.router.supabase")
    def test_medicines_returned_when_adherence_enrichment_fails(self, mock_sb):
        """Active prescriptions must be returned even if secondary adherence lookup errors out."""
        active_meds = [
            {"id": "med-1", "name": "Metformin", "is_active": True, "dosage_amount": 500, "dosage_unit": "mg"},
            {"id": "med-2", "name": "Lisinopril", "is_active": True, "dosage_amount": 10, "dosage_unit": "mg"},
        ]

        # First table call is for medicines (success), second is for reminders/adherence (fails)
        def table_dispatch(name):
            t = MagicMock()
            if name == "medicines":
                t.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=active_meds)
            elif name == "assignments":
                t.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "a1"}])
            else:
                # Reminders or adherence fails
                t.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Adherence timeout")
                t.select.return_value.eq.return_value.gte.return_value.limit.return_value.execute.side_effect = Exception("Adherence timeout")
            return t

        mock_sb.table.side_effect = table_dispatch

        response = client.get(
            f"/v1/medicines/?patient_id={TEST_PATIENT_ID}",
            headers=make_token(role="provider", user_id=TEST_PROVIDER_ID)
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        assert data[0]["name"] == "Metformin"
        assert data[0]["missed_count"] == 0
        assert data[0]["reminders"] == []
        assert data[1]["name"] == "Lisinopril"


class TestProviderPatientFlags:
    @patch("app.provider.router.supabase")
    def test_get_patient_flags_success(self, mock_sb):
        mock_table = MagicMock()
        # Assignment check
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "a1"}]
        )
        # Flags query
        mock_table.select.return_value.eq.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": "flag-1", "flag_type": "dose_drift", "severity": 3}]
        )
        mock_sb.table.return_value = mock_table

        response = client.get(
            f"/v1/provider/patients/{TEST_PATIENT_ID}/flags",
            headers=make_token(role="provider", user_id=TEST_PROVIDER_ID)
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == "flag-1"

    @patch("app.provider.router.supabase")
    def test_resolve_patient_flag_by_path(self, mock_sb):
        mock_table = MagicMock()
        # Assignment check
        mock_table.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "a1"}]
        )
        # Flag lookup
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "flag-1", "user_id": TEST_PATIENT_ID, "resolved_at": None}]
        )
        # Flag update
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        mock_sb.table.return_value = mock_table

        response = client.post(
            f"/v1/provider/patients/{TEST_PATIENT_ID}/flags/flag-1/resolve",
            headers=make_token(role="provider", user_id=TEST_PROVIDER_ID)
        )
        assert response.status_code == 200
        assert response.json()["data"]["resolved"] is True
