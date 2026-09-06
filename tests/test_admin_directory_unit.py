"""
Unit tests for Platform Identity Directory endpoints in app.admin.router.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.main import app

client = TestClient(app)
app.state.limiter.enabled = False

ADMIN_ID = "00000000-0000-0000-0000-000000000100"
PATIENT_ID = "00000000-0000-0000-0000-000000000200"
PROVIDER_ID = "00000000-0000-0000-0000-000000000300"


def make_token(role="admin", user_id=ADMIN_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role},
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}


class TestDirectoryList:
    @patch("app.admin.router.supabase")
    def test_list_directory_users_success(self, mock_sb):
        mock_auth_user = MagicMock()
        mock_auth_user.id = PATIENT_ID
        mock_auth_user.email = "patient@example.com"
        mock_auth_user.last_sign_in_at = "2026-09-01T10:00:00Z"
        mock_sb.auth.admin.list_users.return_value = [mock_auth_user]

        profiles_mock = MagicMock()
        profiles_mock.data = [
            {
                "id": PATIENT_ID,
                "full_name": "Jane Patient",
                "role": "patient",
                "is_active": True,
                "created_at": "2026-08-01T00:00:00Z",
                "updated_at": "2026-08-02T00:00:00Z",
            }
        ]

        assignments_mock = MagicMock()
        assignments_mock.data = [{"patient_id": PATIENT_ID, "provider_id": PROVIDER_ID}]

        provider_profile_mock = MagicMock()
        provider_profile_mock.data = [{"id": PROVIDER_ID, "full_name": "Doctor House"}]

        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.neq.return_value.order.return_value.execute.return_value = profiles_mock
                chain.select.return_value.in_.return_value.execute.return_value = provider_profile_mock
            elif table_name == "assignments":
                chain.select.return_value.eq.return_value.execute.return_value = assignments_mock
            return chain

        mock_sb.table.side_effect = table_side_effect

        response = client.get("/v1/admin/directory?page=1&limit=20", headers=make_token("admin"))
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        items = json_data["data"]["items"]
        assert len(items) == 1
        assert items[0]["full_name"] == "Jane Patient"
        assert items[0]["email"] == "patient@example.com"
        assert items[0]["assigned_provider_name"] == "Doctor House"

    def test_list_directory_forbidden_for_patient(self):
        response = client.get("/v1/admin/directory", headers=make_token("patient", PATIENT_ID))
        assert response.status_code == 403

    def test_list_directory_forbidden_for_provider(self):
        response = client.get("/v1/admin/directory", headers=make_token("provider", PROVIDER_ID))
        assert response.status_code == 403


class TestDirectoryUserDetail:
    @patch("app.admin.router.supabase")
    def test_get_patient_detail_success(self, mock_sb):
        mock_auth_user = MagicMock()
        mock_auth_user.user = MagicMock(email="patient@example.com", last_sign_in_at="2026-09-01T10:00:00Z")
        mock_sb.auth.admin.get_user_by_id.return_value = mock_auth_user

        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                def eq_mock(col, val):
                    eq_chain = MagicMock()
                    if val == PATIENT_ID:
                        eq_chain.execute.return_value = MagicMock(
                            data=[{
                                "id": PATIENT_ID,
                                "full_name": "Jane Patient",
                                "role": "patient",
                                "date_of_birth": "1990-05-15",
                                "blood_group": "O+",
                                "is_active": True,
                                "created_at": "2026-01-01T00:00:00Z",
                            }]
                        )
                    elif val == PROVIDER_ID:
                        eq_chain.execute.return_value = MagicMock(
                            data=[{
                                "id": PROVIDER_ID,
                                "full_name": "Doctor House",
                                "role": "provider",
                                "specialization": "Internal Medicine",
                            }]
                        )
                    else:
                        eq_chain.execute.return_value = MagicMock(data=[])
                    return eq_chain
                chain.select.return_value.eq.side_effect = eq_mock
            elif table_name == "medicines":
                chain.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(count=2)
            elif table_name == "adherence":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{"status": "taken"}, {"status": "taken"}, {"status": "missed"}]
                )
            elif table_name == "assignments":
                chain.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{"provider_id": PROVIDER_ID}]
                )
            elif table_name == "audit_log":
                chain.insert.return_value.execute.return_value = MagicMock()
            return chain

        mock_sb.table.side_effect = table_side_effect

        response = client.get(f"/v1/admin/directory/{PATIENT_ID}", headers=make_token("admin"))
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == PATIENT_ID
        assert data["role"] == "patient"
        assert data["active_medicines_count"] == 2
        assert data["overall_adherence_rate"] == 66.7
        assert data["assigned_provider"]["full_name"] == "Doctor House"
        assert data["age"] is not None

    @patch("app.admin.router.supabase")
    def test_get_user_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}", headers=make_token("admin"))
        assert response.status_code == 404


class TestDirectoryMedicinesAndFeedback:
    @patch("app.admin.router.supabase")
    def test_get_directory_medicines(self, mock_sb):
        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": PATIENT_ID}])
            elif table_name == "medicines":
                chain.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                    data=[{"id": "m1", "name": "Metformin", "dosage": "500mg"}]
                )
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/medicines", headers=make_token("admin"))
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
        assert response.json()["data"][0]["name"] == "Metformin"

    @patch("app.admin.router.supabase")
    def test_get_directory_feedback(self, mock_sb):
        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": PATIENT_ID}])
            elif table_name == "feedback":
                chain.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                    data=[{"id": "f1", "severity": 2, "description": "Mild nausea"}]
                )
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/feedback", headers=make_token("admin"))
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
        assert response.json()["data"][0]["severity"] == 2


class TestDirectoryAdherenceAndExport:
    @patch("app.admin.router.supabase")
    def test_get_directory_adherence(self, mock_sb):
        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": PATIENT_ID}])
            elif table_name == "adherence":
                chain.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(
                    count=1,
                    data=[{"id": "a1", "medicine_id": "m1", "status": "taken", "scheduled_time": "2026-09-01T08:00:00Z"}]
                )
            elif table_name == "medicines":
                chain.select.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[{"id": "m1", "name": "Aspirin"}]
                )
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/adherence?page=1&limit=10", headers=make_token("admin"))
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["medicine_name"] == "Aspirin"

    @patch("app.admin.router.supabase")
    def test_export_directory_adherence_csv(self, mock_sb):
        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": PATIENT_ID}])
            elif table_name == "adherence":
                chain.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                    data=[{
                        "date": "2026-09-01",
                        "medicine_id": "m1",
                        "scheduled_time": "2026-09-01T08:00:00Z",
                        "status": "taken",
                        "logged_at": "2026-09-01T08:05:00Z"
                    }]
                )
            elif table_name == "medicines":
                chain.select.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[{"id": "m1", "name": "Lisinopril"}]
                )
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/adherence/export", headers=make_token("admin"))
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert f"adherence_{PATIENT_ID}.csv" in response.headers["content-disposition"]
        content = response.text
        assert "Date,Medicine,Scheduled Time,Status,Logged At" in content
        assert "Lisinopril" in content

    @patch("app.admin.router.supabase")
    def test_export_directory_adherence_csv_formula_injection_neutralized(self, mock_sb):
        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": PATIENT_ID}])
            elif table_name == "adherence":
                chain.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                    data=[
                        {
                            "date": "2026-09-01",
                            "medicine_id": "m1",
                            "scheduled_time": "2026-09-01T08:00:00Z",
                            "status": "taken",
                            "logged_at": "2026-09-01T08:05:00Z"
                        },
                        {
                            "date": "2026-09-02",
                            "medicine_id": "m2",
                            "scheduled_time": "2026-09-02T08:00:00Z",
                            "status": "taken",
                            "logged_at": "2026-09-02T08:05:00Z"
                        },
                        {
                            "date": "2026-09-03",
                            "medicine_id": "m3",
                            "scheduled_time": "2026-09-03T08:00:00Z",
                            "status": "taken",
                            "logged_at": "2026-09-03T08:05:00Z"
                        }
                    ]
                )
            elif table_name == "medicines":
                chain.select.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[
                        {"id": "m1", "name": "+cmd|' /C calc'!A0"},
                        {"id": "m2", "name": "=1+1"},
                        {"id": "m3", "name": "@SUM(1,2)"},
                    ]
                )
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/adherence/export", headers=make_token("admin"))
        assert response.status_code == 200
        content = response.text
        # Assert each formula injection payload begins with a single quote
        assert "'+cmd|' /C calc'!A0" in content
        assert "'=1+1" in content
        assert "'@SUM(1,2)" in content
        assert "Date,Medicine,Scheduled Time,Status,Logged At" in content


class TestDirectoryStatusChange:
    @patch("app.admin.router.supabase")
    def test_change_status_success(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": PATIENT_ID, "is_active": False}]
        )
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

        payload = {"is_active": False, "reason": "Patient requested suspension"}
        response = client.patch(f"/v1/admin/directory/{PATIENT_ID}/status", json=payload, headers=make_token("admin"))
        assert response.status_code == 200
        assert response.json()["data"]["is_active"] is False

    def test_change_status_missing_reason_fails(self):
        payload = {"is_active": False, "reason": "   "}
        response = client.patch(f"/v1/admin/directory/{PATIENT_ID}/status", json=payload, headers=make_token("admin"))
        assert response.status_code == 400

    @patch("app.admin.router.supabase")
    def test_change_status_user_not_found(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        payload = {"is_active": False, "reason": "Verification failed"}
        response = client.patch(f"/v1/admin/directory/{PATIENT_ID}/status", json=payload, headers=make_token("admin"))
        assert response.status_code == 404


class TestDirectoryAudit:
    @patch("app.admin.router.supabase")
    def test_get_audit_logs_success(self, mock_sb):
        log_entry = {
            "id": "log1",
            "action": "USER_VIEWED",
            "actor_id": ADMIN_ID,
            "target_id": PATIENT_ID,
            "details": {"target_user_id": PATIENT_ID},
            "created_at": "2026-09-06T10:00:00Z",
        }

        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": PATIENT_ID}])
            elif table_name == "audit_log":
                audit_mock = MagicMock(data=[log_entry])
                chain.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = audit_mock
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/audit", headers=make_token("admin"))
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    @patch("app.admin.router.supabase")
    def test_get_audit_logs_user_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/audit", headers=make_token("admin"))
        assert response.status_code == 404

    def test_get_audit_logs_forbidden_non_admin(self):
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/audit", headers=make_token("patient", PATIENT_ID))
        assert response.status_code == 403


class TestDirectoryEmergencyContact:
    @patch("app.admin.router.supabase")
    def test_patient_detail_includes_emergency_contact(self, mock_sb):
        mock_auth_user = MagicMock()
        mock_auth_user.user = MagicMock(email="patient@example.com", last_sign_in_at=None)
        mock_sb.auth.admin.get_user_by_id.return_value = mock_auth_user

        ec_data = {
            "full_name": "Jane Doe Emergency",
            "email": "emergency@example.com",
            "phone": "+1234567890",
            "relationship": "Spouse",
            "is_verified": True,
        }

        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                def eq_mock(col, val):
                    eq_chain = MagicMock()
                    eq_chain.execute.return_value = MagicMock(
                        data=[{"id": PATIENT_ID, "full_name": "Jane Patient", "role": "patient", "is_active": True, "created_at": "2026-01-01T00:00:00Z"}]
                    )
                    return eq_chain
                chain.select.return_value.eq.side_effect = eq_mock
            elif table_name == "emergency_contacts":
                chain.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[ec_data])
            elif table_name == "medicines":
                chain.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(count=0)
            elif table_name == "adherence":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            elif table_name == "assignments":
                chain.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
            elif table_name == "audit_log":
                chain.insert.return_value.execute.return_value = MagicMock()
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}", headers=make_token("admin"))
        assert response.status_code == 200
        data = response.json()["data"]
        assert "emergency_contact" in data
        ec = data["emergency_contact"]
        assert ec["full_name"] == "Jane Doe Emergency"
        assert ec["relationship"] == "Spouse"
        assert ec["is_verified"] is True
        assert "mfa_secret" not in data


class TestDirectoryAdherenceDoseLabel:
    @patch("app.admin.router.supabase")
    def test_adherence_includes_dose_label_and_notes(self, mock_sb):
        def table_side_effect(table_name):
            chain = MagicMock()
            if table_name == "profiles":
                chain.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": PATIENT_ID}])
            elif table_name == "adherence":
                chain.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(
                    count=1,
                    data=[{
                        "id": "a1",
                        "medicine_id": "m1",
                        "reminder_id": "rem1",
                        "status": "taken",
                        "scheduled_time": "2026-09-01T08:00:00Z",
                        "correction_note": "Took 30 min late",
                    }]
                )
            elif table_name == "medicines":
                chain.select.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[{"id": "m1", "name": "Metformin"}]
                )
            elif table_name == "reminders":
                chain.select.return_value.in_.return_value.execute.return_value = MagicMock(
                    data=[{"id": "rem1", "dose_label": "Morning Dose", "medicine_id": "m1"}]
                )
            return chain

        mock_sb.table.side_effect = table_side_effect
        response = client.get(f"/v1/admin/directory/{PATIENT_ID}/adherence?page=1&limit=10", headers=make_token("admin"))
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["dose_label"] == "Morning Dose"
        assert items[0]["notes"] == "Took 30 min late"
        assert items[0]["medicine_name"] == "Metformin"

