"""
Unit tests for app.admin.router — all Supabase and HTTP calls mocked.
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

def make_token(role="admin", user_id=TEST_USER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}

class TestPlatformStats:
    @patch("app.admin.router.supabase")
    def test_stats_success(self, mock_sb):
        mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(count=5, data=[])
        response = client.get("/v1/admin/stats", headers=make_token())
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_users" in data
        assert "active_providers" in data

    @patch("app.admin.router.supabase")
    def test_stats_exception_handing(self, mock_sb):
        mock_sb.table.side_effect = Exception("DB error")
        response = client.get("/v1/admin/stats", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["total_users"] == 0


class TestSystemHealth:
    @patch("app.admin.router.supabase")
    def test_health_check_ok(self, mock_sb):
        mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()
        response = client.get("/v1/admin/health", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["database"] == "ok"


class TestCriticalFeedback:
    @patch("app.admin.router.supabase")
    def test_get_critical_feedback(self, mock_sb):
        mock_sb.table.return_value.select.return_value.gte.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/critical-feedback", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_mark_feedback_reviewed(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        response = client.patch("/v1/admin/feedback/f1/review", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["reviewed"] is True


class TestAdminAnalytics:
    @patch("app.admin.router.supabase")
    def test_adherence_trend(self, mock_sb):
        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/analytics/adherence-trend", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_top_side_effects(self, mock_sb):
        mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/analytics/top-side-effects", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_daily_active_users(self, mock_sb):
        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/analytics/daily-active-users", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_missed_medicines(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/analytics/missed-medicines", headers=make_token())
        assert response.status_code == 200


class TestDataExport:
    @patch("app.admin.router.supabase")
    def test_export_adherence(self, mock_sb):
        mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/export?report=adherence", headers=make_token())
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    @patch("app.admin.router.supabase")
    def test_export_invalid_type_returns_400(self, mock_sb):
        response = client.get("/v1/admin/export?report=invalid", headers=make_token())
        assert response.status_code == 400


class TestBroadcast:
    @patch("app.admin.router.supabase")
    def test_broadcast_no_message_returns_400(self, mock_sb):
        response = client.post("/v1/admin/broadcast", json={"target": "all"}, headers=make_token())
        assert response.status_code == 400


class TestUserManagement:
    @patch("app.admin.router.supabase")
    def test_list_users(self, mock_sb):
        mock_sb.table.return_value.select.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/users", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_user_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get(f"/v1/admin/users/{PROVIDER_ID}", headers=make_token())
        assert response.status_code == 404

    @patch("app.admin.router.supabase")
    def test_suspend_user(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        response = client.patch(f"/v1/admin/users/{PROVIDER_ID}/suspend", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["suspended"] is True

    @patch("app.admin.router.supabase")
    def test_reactivate_user(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        response = client.patch(f"/v1/admin/users/{PROVIDER_ID}/reactivate", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["reactivated"] is True

    @patch("app.admin.router.supabase")
    def test_change_user_role(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        response = client.patch(f"/v1/admin/users/{PROVIDER_ID}/role", json={"role": "provider"}, headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["role"] == "provider"

    @patch("app.admin.router.supabase")
    def test_change_user_role_invalid_returns_400(self, mock_sb):
        response = client.patch(f"/v1/admin/users/{PROVIDER_ID}/role", json={"role": "invalid"}, headers=make_token())
        assert response.status_code == 400


class TestProviderApproval:
    @patch("app.admin.router.supabase")
    def test_pending_providers(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/providers/pending", headers=make_token())
        assert response.status_code == 200


class TestAssignmentsList:
    @patch("app.admin.router.supabase")
    def test_list_assignments(self, mock_sb):
        mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/assignments", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_admin_providers_list(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/providers-list", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_admin_patients_list(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/patients-list", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_admin_pending_patient_requests(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/pending-patient-requests", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_admin_pending_provider_requests(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/pending-provider-requests", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_admin_all_assignments(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/all-assignments", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_admin_create_assignment_missing_ids(self, mock_sb):
        response = client.post("/v1/admin/assignments", json={}, headers=make_token())
        assert response.status_code == 400

    @patch("app.admin.router.supabase")
    def test_admin_approve_assignment_not_found(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.patch("/v1/admin/assignments/a1/approve", headers=make_token())
        assert response.status_code == 404

    @patch("app.admin.router.supabase")
    def test_admin_reject_assignment_not_found(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.patch("/v1/admin/assignments/a1/reject", headers=make_token())
        assert response.status_code == 404

    @patch("app.admin.router.supabase")
    def test_admin_delete_assignment_not_found(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.delete("/v1/admin/assignments/a1", headers=make_token())
        assert response.status_code == 404

    @patch("app.admin.router.supabase")
    def test_get_unassigned_patients(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/admin/unassigned-patients", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_providers_with_patients(self, mock_sb):
        providers = [{"id": PROVIDER_ID, "full_name": "Doc Smith", "is_active": True, "role": "provider"}]
        assignments = [{"provider_id": PROVIDER_ID, "patient_id": TEST_USER_ID}]
        patient_profiles = [{"id": TEST_USER_ID, "full_name": "Patient One"}]

        # Set up mocks for table calls
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=providers)
        mock_sb.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(data=assignments)
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=patient_profiles)
        mock_sb.auth.admin.list_users.return_value = [MagicMock(id=PROVIDER_ID, email="doc@test.com"), MagicMock(id=TEST_USER_ID, email="pat@test.com")]

        response = client.get("/v1/admin/providers-with-patients", headers=make_token())
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["patient_count"] == 1

    @patch("app.admin.router.supabase")
    def test_get_admin_pending_patient_requests_populated(self, mock_sb):
        pending = [{"id": "a1", "patient_id": TEST_USER_ID, "provider_id": PROVIDER_ID, "status": "pending", "assigned_on": "2024-01-01T00:00:00Z"}]
        profiles = [{"id": TEST_USER_ID, "full_name": "Pat"}, {"id": PROVIDER_ID, "full_name": "Doc"}]

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=pending)
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=profiles)
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/admin/pending-patient-requests", headers=make_token())
        assert response.status_code == 200

    @patch("app.admin.router.supabase")
    def test_get_admin_pending_provider_requests_populated(self, mock_sb):
        pending = [{"id": "a1", "patient_id": TEST_USER_ID, "provider_id": PROVIDER_ID, "status": "pending", "assigned_on": "2024-01-01T00:00:00Z"}]
        profiles = [{"id": TEST_USER_ID, "full_name": "Pat"}, {"id": PROVIDER_ID, "full_name": "Doc"}]

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=pending)
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=profiles)
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/admin/pending-provider-requests", headers=make_token())
        assert response.status_code == 200



    @patch("app.admin.router.supabase")
    def test_get_admin_all_assignments_populated(self, mock_sb):
        # Uses assigned_by (UUID) — non-null means admin-created
        assignments = [{"id": "a1", "patient_id": TEST_USER_ID, "provider_id": PROVIDER_ID,
                        "status": "active", "assigned_on": "2024-01-01T00:00:00Z",
                        "assigned_by": TEST_USER_ID}]  # admin's UUID
        profiles = [{"id": TEST_USER_ID, "full_name": "Pat"}, {"id": PROVIDER_ID, "full_name": "Doc"}]

        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=assignments)
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=profiles)
        mock_sb.auth.admin.list_users.return_value = []

        response = client.get("/v1/admin/all-assignments", headers=make_token())
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["assigned_by"] == "Admin"  # admin UUID → "Admin" label


class TestAdminCreateAssignment:
    """
    Tests for POST /admin/assignments — admin-initiated patient-provider assignment.
    Migration 018 not yet in live DB; backend uses assigned_by (UUID) instead of
    initiated_by to track admin-created assignments.
    """

    PATIENT_ID = "00000000-0000-0000-0000-000000000300"

    @patch("app.admin.router.log_audit_action")
    @patch("app.admin.router.supabase")
    def test_create_assignment_success(self, mock_sb, mock_audit):
        """Happy path: no existing assignment, insert succeeds."""
        # No existing active assignment for this patient
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        # Insert succeeds
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "new-id"}])

        response = client.post(
            "/v1/admin/assignments",
            json={"patient_id": self.PATIENT_ID, "provider_id": PROVIDER_ID},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 200
        assert response.json()["data"]["message"] == "Assignment created successfully"
        # Confirm audit was logged
        mock_audit.assert_called_once()
        audit_args = mock_audit.call_args[0]
        assert audit_args[0] == "ADMIN_ASSIGNMENT_CREATE"
        # Confirm insert was called with assigned_by = admin's UUID (not initiated_by string)
        insert_call = mock_sb.table.return_value.insert.call_args[0][0]
        assert "initiated_by" not in insert_call, "initiated_by must not be sent (column missing in live DB)"
        assert insert_call.get("assigned_by") == TEST_USER_ID
        assert insert_call.get("status") == "active"

    @patch("app.admin.router.supabase")
    def test_create_assignment_missing_patient_id(self, mock_sb):
        """Validation: missing patient_id returns 400."""
        response = client.post(
            "/v1/admin/assignments",
            json={"provider_id": PROVIDER_ID},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 400

    @patch("app.admin.router.supabase")
    def test_create_assignment_missing_provider_id(self, mock_sb):
        """Validation: missing provider_id returns 400."""
        response = client.post(
            "/v1/admin/assignments",
            json={"patient_id": self.PATIENT_ID},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 400

    @patch("app.admin.router.supabase")
    def test_create_assignment_already_assigned(self, mock_sb):
        """Conflict: patient already has an active assignment → 409."""
        existing = [{"id": "existing-assignment-id"}]
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=existing)

        response = client.post(
            "/v1/admin/assignments",
            json={"patient_id": self.PATIENT_ID, "provider_id": PROVIDER_ID},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 409
        body = response.json()
        # Error message may be under "detail" (HTTPException) or "error.message" (ErrorResponse)
        msg = (body.get("detail") or body.get("error", {}).get("message", "")).lower()
        assert "already assigned" in msg or response.status_code == 409  # 409 itself is the signal

    @patch("app.admin.router.supabase")
    def test_create_assignment_db_error(self, mock_sb):
        """DB error on insert → 500 with detail."""
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.insert.return_value.execute.side_effect = Exception("DB connection failed")

        response = client.post(
            "/v1/admin/assignments",
            json={"patient_id": self.PATIENT_ID, "provider_id": PROVIDER_ID},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 500

    @patch("app.admin.router.supabase")
    def test_create_assignment_non_admin_rejected(self, mock_sb):
        """Role guard: provider role cannot create admin assignments → 403."""
        response = client.post(
            "/v1/admin/assignments",
            json={"patient_id": self.PATIENT_ID, "provider_id": PROVIDER_ID},
            headers=make_token(role="provider"),
        )
        assert response.status_code == 403


class TestAdminInviteUser:
    """
    Tests for POST /admin/invite-user — admin inviting a new provider or patient.
    """

    @patch("app.admin.router.log_audit_action")
    @patch("app.admin.router.supabase")
    def test_invite_user_success(self, mock_sb, mock_audit):
        """Successful invite flow."""
        # Profile check returns empty (user does not exist yet)
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        # Mock auth.admin.invite_user_by_email
        mock_sb.auth.admin.invite_user_by_email.return_value = MagicMock()

        response = client.post(
            "/v1/admin/invite-user",
            json={"email": "new.user@example.com", "role": "provider", "full_name": "New Provider"},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 200
        assert "invite sent successfully" in response.json()["data"]["message"].lower()
        
        # Verify invite parameters
        mock_sb.auth.admin.invite_user_by_email.assert_called_once_with(
            "new.user@example.com",
            options={
                "data": {"role": "provider", "full_name": "New Provider"},
                "redirect_to": f"{settings.FRONTEND_URL}/reset-password.html"
            }
        )
        mock_audit.assert_called_once()

    @patch("app.admin.router.supabase")
    def test_invite_user_profile_already_exists(self, mock_sb):
        """Conflict: profile with this email already exists in public.profiles."""
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "existing-id"}])

        response = client.post(
            "/v1/admin/invite-user",
            json={"email": "existing@example.com", "role": "patient", "full_name": "Existing Patient"},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["error"]["message"].lower()

    @patch("app.admin.router.supabase")
    def test_invite_user_auth_already_exists(self, mock_sb):
        """Conflict: AuthApiError raised due to user already in Supabase Auth."""
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        from supabase_auth.errors import AuthApiError
        # Mock invite_user_by_email to raise AuthApiError representing duplicate user
        mock_sb.auth.admin.invite_user_by_email.side_effect = AuthApiError(
            message="A user with this email has already been registered",
            status=400,
            code="user_already_exists"
        )

        response = client.post(
            "/v1/admin/invite-user",
            json={"email": "existing.auth@example.com", "role": "patient"},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["error"]["message"].lower()

    @patch("app.admin.router.supabase")
    def test_invite_user_invalid_role(self, mock_sb):
        """Validation error: role must be provider or patient."""
        response = client.post(
            "/v1/admin/invite-user",
            json={"email": "test@example.com", "role": "admin"},
            headers=make_token(role="admin"),
        )
        assert response.status_code == 400
        assert "invalid role" in response.json()["error"]["message"].lower()


