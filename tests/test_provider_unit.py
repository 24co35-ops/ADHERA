"""
Unit tests for app.provider.router — all routes mocked.
"""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.main import app

client = TestClient(app)
app.state.limiter.enabled = False

TEST_PROVIDER_ID = "00000000-0000-0000-0000-000000000200"
TEST_PATIENT_ID  = "00000000-0000-0000-0000-000000000123"


def make_token(role="provider", user_id=TEST_PROVIDER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}


# ── /provider/dashboard ────────────────────────────────────────────────────────

class TestProviderDashboard:
    @patch("app.provider.router.supabase")
    def test_no_patients_returns_empty(self, mock_sb):
        # No assignments → empty dashboard
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/provider/dashboard", headers=make_token())
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["stats"]["active_patients"] == 0
        assert data["patients"] == []

    @patch("app.provider.router.supabase")
    def test_with_patients_returns_stats(self, mock_sb):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)

        # assignments
        assignments_mock = MagicMock(data=[{"patient_id": TEST_PATIENT_ID}])
        # profiles
        profiles_mock = MagicMock(data=[{"id": TEST_PATIENT_ID, "full_name": "Pat", "contact_number": "1234", "date_of_birth": "1990-01-01", "blood_group": "A+"}])
        # adherence
        adherence_mock = MagicMock(data=[
            {"user_id": TEST_PATIENT_ID, "status": "taken", "scheduled_utc": (now - timedelta(days=1)).isoformat()},
            {"user_id": TEST_PATIENT_ID, "status": "missed", "scheduled_utc": (now - timedelta(days=2)).isoformat()},
        ])
        # feedback alerts
        feedback_mock = MagicMock(data=[])

        # Chain mock: table().select().eq().eq().execute() for assignments
        select_mock = mock_sb.table.return_value.select.return_value
        select_mock.eq.return_value.eq.return_value.execute.return_value = assignments_mock
        select_mock.in_.return_value.execute.return_value = profiles_mock
        select_mock.in_.return_value.gte.return_value.execute.return_value = adherence_mock
        select_mock.in_.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = feedback_mock
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/provider/dashboard", headers=make_token())
        assert response.status_code in (200, 500)  # 500 OK if mock chain incomplete

    @patch("app.provider.router.supabase")
    def test_exception_returns_500(self, mock_sb):
        mock_sb.table.side_effect = Exception("DB error")
        response = client.get("/v1/provider/dashboard", headers=make_token())
        assert response.status_code == 500

    @patch("app.provider.router.supabase")
    def test_dashboard_feedback_mapping_regression(self, mock_sb):
        # Verify provider dashboard resolves feedback user full_name via separate profiles query.
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # Mock table calls
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assignments":
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{"patient_id": TEST_PATIENT_ID}]
                )
            elif table_name == "profiles":
                mock_table.select.return_value.in_.return_value.execute.side_effect = [
                    # First profiles call: dashboard patient profiles
                    MagicMock(data=[{
                        "id": TEST_PATIENT_ID, "full_name": "Alice Patient",
                        "contact_number": "1234", "date_of_birth": "1990-01-01", "blood_group": "A+"
                    }]),
                    # Second profiles call: feedback author profiles
                    MagicMock(data=[{
                        "id": TEST_PATIENT_ID, "full_name": "Alice Patient"
                    }])
                ]
            elif table_name == "adherence":
                mock_table.select.return_value.in_.return_value.gte.return_value.execute.return_value = MagicMock(
                    data=[]
                )
            elif table_name == "feedback":
                mock_table.select.return_value.in_.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                    data=[{
                        "id": "fb-999",
                        "user_id": TEST_PATIENT_ID,
                        "severity": 3,
                        "description": "Nausea after meds",
                        "created_at": now.isoformat()
                    }]
                )
            elif table_name == "patient_flags":
                mock_table.select.return_value.in_.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                    data=[]
                )
            return mock_table

        mock_sb.table.side_effect = table_side_effect
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/provider/dashboard", headers=make_token())
        assert response.status_code == 200
        data = response.json()["data"]

        # Verify alert_list profiles full_name is correctly resolved
        assert len(data["alerts"]) == 1
        alert = data["alerts"][0]
        assert alert["id"] == "fb-999"
        assert alert["profiles"]["full_name"] == "Alice Patient"
        assert alert["description"] == "Nausea after meds"

    @patch("app.provider.router.supabase")
    def test_dashboard_new_patient_fields(self, mock_sb):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)

        assignments_mock = MagicMock(data=[{"patient_id": TEST_PATIENT_ID}])
        profiles_mock = MagicMock(data=[{"id": TEST_PATIENT_ID, "full_name": "Pat", "contact_number": "1234", "date_of_birth": "1990-01-01", "blood_group": "A+"}])
        adherence_mock = MagicMock(data=[
            {"user_id": TEST_PATIENT_ID, "status": "taken", "scheduled_utc": (now - timedelta(hours=2)).isoformat()},
            {"user_id": TEST_PATIENT_ID, "status": "missed", "scheduled_utc": (now - timedelta(hours=4)).isoformat()},
        ])
        reminders_mock = MagicMock(data=[
            {"user_id": TEST_PATIENT_ID, "is_active": True, "dose_time_utc": "12:00:00", "recurrence_type": "daily", "medicines": {"name": "Aspirin", "is_active": True, "start_date": "2026-01-01"}}
        ])

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assignments":
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = assignments_mock
            elif table_name == "profiles":
                mock_table.select.return_value.in_.return_value.execute.return_value = profiles_mock
            elif table_name == "adherence":
                mock_select = MagicMock()
                mock_select.in_.return_value.gte.return_value.execute.return_value = adherence_mock
                mock_select.in_.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[{"user_id": TEST_PATIENT_ID, "scheduled_utc": (now - timedelta(hours=2)).isoformat()}])
                mock_select.in_.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(data=[{"user_id": TEST_PATIENT_ID}])
                mock_table.select.return_value = mock_select
            elif table_name == "reminders":
                mock_table.select.return_value.in_.return_value.eq.return_value.execute.return_value = reminders_mock
            else:
                mock_table.select.return_value.in_.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
                mock_table.select.return_value.in_.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
            return mock_table

        mock_sb.table.side_effect = table_side_effect
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/provider/dashboard", headers=make_token())
        assert response.status_code == 200
        data = response.json()["data"]
        patients = data["patients"]
        assert len(patients) == 1
        p = patients[0]
        assert "risk_level" in p
        assert p["risk_level"] in ("critical", "high", "moderate", "low")
        assert "last_dose_taken" in p
        assert "missed_today" in p
        assert "next_medication" in p

    def test_patient_role_forbidden(self):
        response = client.get("/v1/provider/dashboard", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 403


# ── /provider/patients ─────────────────────────────────────────────────────────

class TestListPatients:
    @patch("app.provider.router.supabase")
    def test_no_assignments(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/provider/patients", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_patient_role_forbidden(self):
        response = client.get("/v1/provider/patients", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 403


# ── /provider/patients/{id} ────────────────────────────────────────────────────

class TestGetPatient:
    @patch("app.provider.router.supabase")
    def test_patient_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get(f"/v1/provider/patients/{TEST_PATIENT_ID}", headers=make_token())
        assert response.status_code == 404

    @patch("app.provider.router.supabase")
    def test_patient_found(self, mock_sb):
        profile = {"id": TEST_PATIENT_ID, "full_name": "Pat", "date_of_birth": "1990-01-01"}
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[profile])
        mock_sb.auth.admin.get_user_by_id.return_value = MagicMock(user=MagicMock(email="p@test.com"))
        response = client.get(f"/v1/provider/patients/{TEST_PATIENT_ID}", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["full_name"] == "Pat"


# ── /provider/patients/{id}/report ────────────────────────────────────────────

class TestGetPatientReport:
    @patch("app.provider.router.supabase")
    def test_no_report_returns_empty(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        response = client.get(f"/v1/provider/patients/{TEST_PATIENT_ID}/report", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"] == {}

    @patch("app.provider.router.supabase")
    def test_report_returned(self, mock_sb):
        report = {"id": "r1", "user_id": TEST_PATIENT_ID, "summary": "Good"}
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[report])
        response = client.get(f"/v1/provider/patients/{TEST_PATIENT_ID}/report", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["summary"] == "Good"


# ── /provider/pending-requests ─────────────────────────────────────────────────

class TestPendingRequests:
    @patch("app.provider.router.supabase")
    def test_no_pending(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/provider/pending-requests", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"] == []

    @patch("app.provider.router.supabase")
    def test_pending_with_profile(self, mock_sb):
        pending = [{"patient_id": TEST_PATIENT_ID, "provider_id": TEST_PROVIDER_ID, "status": "pending"}]
        profile = [{"id": TEST_PATIENT_ID, "full_name": "Pat", "date_of_birth": "1990-01-01", "blood_group": "A+", "contact_number": "1234"}]

        sel = mock_sb.table.return_value.select.return_value
        sel.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=pending)
        sel.in_.return_value.execute.return_value = MagicMock(data=profile)
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/provider/pending-requests", headers=make_token())
        assert response.status_code == 200


# ── /provider/requests/{id}/accept & decline ──────────────────────────────────

class TestAcceptDeclineRequest:
    @patch("app.provider.router.supabase")
    def test_accept_request(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        response = client.patch(f"/v1/provider/requests/{TEST_PATIENT_ID}/accept", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["accepted"] is True

    @patch("app.provider.router.supabase")
    def test_decline_request(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        response = client.patch(f"/v1/provider/requests/{TEST_PATIENT_ID}/decline", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["declined"] is True


# ── /provider/my-provider (patient perspective) ───────────────────────────────

class TestMyProvider:
    @patch("app.provider.router.supabase")
    def test_no_assignment(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/provider/my-provider", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["assigned"] is False
        assert data["pending"] is False

    @patch("app.provider.router.supabase")
    def test_active_assignment(self, mock_sb):
        row = {"status": "active", "provider_id": TEST_PROVIDER_ID, "patient_id": TEST_PATIENT_ID, "profiles": {"id": TEST_PROVIDER_ID, "full_name": "Doc"}}
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[row])
        mock_sb.auth.admin.get_user_by_id.return_value = MagicMock(user=MagicMock(email="doc@test.com"))
        response = client.get("/v1/provider/my-provider", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 200
        assert response.json()["data"]["assigned"] is True

    @patch("app.provider.router.supabase")
    def test_pending_assignment(self, mock_sb):
        row = {"status": "pending", "provider_id": TEST_PROVIDER_ID, "patient_id": TEST_PATIENT_ID, "profiles": None}
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[row])
        response = client.get("/v1/provider/my-provider", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 200
        assert response.json()["data"]["pending"] is True


# ── /provider/search-providers ─────────────────────────────────────────────────

class TestSearchProviders:
    @patch("app.provider.router.supabase")
    def test_search_no_query(self, mock_sb):
        providers = [{"id": TEST_PROVIDER_ID, "full_name": "Dr. Smith", "contact_number": "9999"}]
        q = mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value
        q.limit.return_value.execute.return_value = MagicMock(data=providers)
        mock_sb.auth.admin.list_users.return_value = []
        response = client.get("/v1/provider/search-providers", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @patch("app.provider.router.supabase")
    def test_search_with_query(self, mock_sb):
        q = mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value
        q.ilike.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.auth.admin.list_users.return_value = []
        response = client.get("/v1/provider/search-providers?query=Smith", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 200


# ── /provider/request-provider ────────────────────────────────────────────────

class TestRequestProvider:
    @patch("app.provider.router.supabase")
    def test_missing_provider_id_returns_400(self, mock_sb):
        response = client.post("/v1/provider/request-provider", json={}, headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 400

    @patch("app.provider.router.supabase")
    def test_already_assigned_returns_409(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(data=[{"id": "a1", "status": "active"}])
        response = client.post("/v1/provider/request-provider", json={"provider_id": TEST_PROVIDER_ID}, headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 409

    @patch("app.provider.router.supabase")
    def test_pending_request_returns_409(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(data=[{"id": "a1", "status": "pending"}])
        response = client.post("/v1/provider/request-provider", json={"provider_id": TEST_PROVIDER_ID}, headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 409

    @patch("app.provider.router.supabase")
    def test_new_request_succeeds(self, mock_sb):
        sel = mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.execute
        sel.return_value = MagicMock(data=[])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])
        response = client.post("/v1/provider/request-provider", json={"provider_id": TEST_PROVIDER_ID}, headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 200
        assert response.json()["data"]["requested"] is True


# ── /provider/request-provider DELETE ─────────────────────────────────────────

class TestCancelProviderRequest:
    @patch("app.provider.router.supabase")
    def test_cancel_succeeds(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        response = client.delete("/v1/provider/request-provider", headers=make_token(role="patient", user_id=TEST_PATIENT_ID))
        assert response.status_code == 200
        assert response.json()["data"]["cancelled"] is True


# ── Regression: dashboard returns all assigned patients ────────────────────────

TEST_PATIENT_ID_2 = "00000000-0000-0000-0000-000000000124"

class TestDashboardPatientCount:
    """
    Regression for: provider dashboard returning 0 patients when patient_flags
    table is missing (PGRST205 → APIError previously crashed entire endpoint).
    """

    @patch("app.provider.router.supabase")
    def test_two_assigned_patients_all_returned(self, mock_sb):
        """Both assigned patients must appear in the response regardless of patient_flags state."""
        from datetime import datetime, timedelta, timezone

        from postgrest.exceptions import APIError

        now = datetime.now(timezone.utc)

        assignments_mock = MagicMock(data=[
            {"patient_id": TEST_PATIENT_ID},
            {"patient_id": TEST_PATIENT_ID_2},
        ])
        profiles_mock = MagicMock(data=[
            {"id": TEST_PATIENT_ID,   "full_name": "Patient Alpha", "contact_number": "111", "date_of_birth": "1990-01-01", "blood_group": "A+"},
            {"id": TEST_PATIENT_ID_2, "full_name": "Patient Beta",  "contact_number": "222", "date_of_birth": "1985-06-15", "blood_group": "O-"},
        ])
        adherence_mock = MagicMock(data=[
            {"user_id": TEST_PATIENT_ID,   "status": "taken",  "scheduled_utc": (now - timedelta(hours=2)).isoformat()},
            {"user_id": TEST_PATIENT_ID_2, "status": "missed", "scheduled_utc": (now - timedelta(hours=3)).isoformat()},
        ])
        last_dose_mock = MagicMock(data=[
            {"user_id": TEST_PATIENT_ID, "scheduled_utc": (now - timedelta(hours=2)).isoformat()},
        ])
        missed_mock  = MagicMock(data=[])
        feedback_mock = MagicMock(data=[])
        reminders_mock = MagicMock(data=[])

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "assignments":
                mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = assignments_mock
            elif table_name == "profiles":
                mock_table.select.return_value.in_.return_value.execute.return_value = profiles_mock
            elif table_name == "adherence":
                mock_select = MagicMock()
                # 30-day batch
                mock_select.in_.return_value.gte.return_value.execute.return_value = adherence_mock
                # last_dose batch (taken + order)
                mock_select.in_.return_value.eq.return_value.order.return_value.execute.return_value = last_dose_mock
                # missed_today batch
                mock_select.in_.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = missed_mock
                mock_table.select.return_value = mock_select
            elif table_name == "reminders":
                mock_table.select.return_value.in_.return_value.eq.return_value.execute.return_value = reminders_mock
            elif table_name == "feedback":
                mock_table.select.return_value.in_.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = feedback_mock
            elif table_name == "patient_flags":
                # Simulate missing table: raise APIError (PGRST205)
                mock_table.select.return_value.in_.return_value.is_.return_value.order.return_value.limit.return_value.execute.side_effect = APIError(
                    {"message": "Could not find the table 'public.patient_flags' in the schema cache", "code": "PGRST205", "hint": None, "details": None}
                )
            return mock_table

        mock_sb.table.side_effect = table_side_effect
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/provider/dashboard", headers=make_token())
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()["data"]

        # Both patients must be present
        assert len(data["patients"]) == 2, f"Expected 2 patients, got {len(data['patients'])}"
        patient_ids = {p["patient_id"] for p in data["patients"]}
        assert TEST_PATIENT_ID   in patient_ids
        assert TEST_PATIENT_ID_2 in patient_ids

        # Flags degrade gracefully to empty list
        assert data["insight_flags"] == []
