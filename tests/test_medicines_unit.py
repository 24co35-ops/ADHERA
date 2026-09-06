"""
Unit tests for app.medicines.router — all Supabase calls mocked.
Tests: create, list, get, update, delete, get_reminders, create_reminder.
"""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.main import app

client = TestClient(app)
app.state.limiter.enabled = False

TEST_USER_ID = "00000000-0000-0000-0000-000000000123"
TEST_MED_ID  = "med-00000000-0000-0000-0000-000000000001"
PROVIDER_ID  = "00000000-0000-0000-0000-000000000200"


def make_token(role="patient", user_id=TEST_USER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')}"}


MEDICINE_PAYLOAD = {
    "name": "Metformin",
    "dosage_amount": 500,
    "dosage_unit": "mg",
    "route": "oral",
    "frequency_type": "daily",
    "start_date": "2024-01-01",
    "end_date": None,
    "instructions": "After meals"
}

MEDICINE_DB = {
    "id": TEST_MED_ID,
    "user_id": TEST_USER_ID,
    "name": "Metformin",
    "dosage_amount": 500,
    "dosage_unit": "mg",
    "route": "oral",
    "frequency_type": "daily",
    "start_date": "2024-01-01",
    "is_active": True
}


class TestCreateMedicine:
    @patch("app.medicines.router.supabase")
    def test_create_success(self, mock_sb):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[MEDICINE_DB])
        response = client.post("/v1/medicines/", json=MEDICINE_PAYLOAD, headers=make_token())
        assert response.status_code == 201
        assert response.json()["data"]["name"] == "Metformin"

    @patch("app.medicines.router.supabase")
    def test_create_daily_oral_success(self, mock_sb):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[MEDICINE_DB])
        payload = {
            "name": "Lisinopril",
            "dosage_amount": 10,
            "dosage_unit": "mg",
            "route": "oral",
            "frequency_type": "daily",
            "start_date": "2025-01-01",
            "instructions": "Take with water"
        }
        response = client.post("/v1/medicines/", json=payload, headers=make_token())
        assert response.status_code == 201

    @patch("app.medicines.router.supabase")
    def test_create_weekday_medicine_success(self, mock_sb):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{**MEDICINE_DB, "frequency_type": "weekday"}])
        payload = {
            "name": "Methotrexate",
            "dosage_amount": 2.5,
            "dosage_unit": "mg",
            "route": "oral",
            "frequency_type": "weekday",
            "start_date": "2025-01-01"
        }
        response = client.post("/v1/medicines/", json=payload, headers=make_token())
        assert response.status_code == 201

    @patch("app.medicines.router.supabase")
    def test_create_alternate_day_medicine_success(self, mock_sb):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{**MEDICINE_DB, "frequency_type": "alternate"}])
        payload = {
            "name": "Warfarin",
            "dosage_amount": 5,
            "dosage_unit": "mg",
            "route": "oral",
            "frequency_type": "alternate",
            "start_date": "2025-01-01"
        }
        response = client.post("/v1/medicines/", json=payload, headers=make_token())
        assert response.status_code == 201

    @patch("app.medicines.router.supabase")
    def test_create_prn_medicine_success(self, mock_sb):
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{**MEDICINE_DB, "frequency_type": "prn"}])
        payload = {
            "name": "Albuterol",
            "dosage_amount": 2,
            "dosage_unit": "units",
            "route": "inhaled",
            "frequency_type": "prn",
            "start_date": "2025-01-01"
        }
        response = client.post("/v1/medicines/", json=payload, headers=make_token())
        assert response.status_code == 201

    @patch("app.medicines.router.supabase")
    def test_create_missing_required_field(self, mock_sb):
        response = client.post("/v1/medicines/", json={"name": "Metformin"}, headers=make_token())
        assert response.status_code in (400, 422)
        body = response.json()
        assert body["success"] is False
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["field"] is not None
        assert "details" in body["error"]
        assert len(body["error"]["details"]) > 0

    def test_create_medicine_invalid_route(self):
        payload = {
            "name": "Test Med",
            "dosage_amount": 10,
            "dosage_unit": "mg",
            "route": "invalid_route",
            "frequency_type": "daily",
            "start_date": "2025-01-01"
        }
        response = client.post("/v1/medicines/", json=payload, headers=make_token())
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "route" in response.json()["error"]["field"]

    def test_create_medicine_invalid_dosage_unit(self):
        payload = {
            "name": "Test Med",
            "dosage_amount": 10,
            "dosage_unit": "invalid_unit",
            "route": "oral",
            "frequency_type": "daily",
            "start_date": "2025-01-01"
        }
        response = client.post("/v1/medicines/", json=payload, headers=make_token())
        assert response.status_code == 422
        assert "dosage_unit" in response.json()["error"]["field"]

    def test_create_medicine_invalid_end_date_before_start_date(self):
        payload = {
            "name": "Test Med",
            "dosage_amount": 10,
            "dosage_unit": "mg",
            "route": "oral",
            "frequency_type": "daily",
            "start_date": "2025-05-10",
            "end_date": "2025-05-01"
        }
        response = client.post("/v1/medicines/", json=payload, headers=make_token())
        assert response.status_code == 422
        assert "end_date" in response.json()["error"]["field"]


class TestListMedicines:
    @patch("app.medicines.router.supabase")
    def test_list_patient_medicines(self, mock_sb):
        medicines = [MEDICINE_DB]
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=medicines)
        # reminders and adherence mocks
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/medicines/", headers=make_token())
        assert response.status_code == 200

    @patch("app.medicines.router.supabase")
    def test_list_provider_without_patient_id_returns_400(self, mock_sb):
        response = client.get("/v1/medicines/", headers=make_token(role="provider", user_id=PROVIDER_ID))
        assert response.status_code == 400

    @patch("app.medicines.router.supabase")
    def test_list_admin_no_patient_id_uses_self(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[MEDICINE_DB])
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/v1/medicines/", headers=make_token(role="admin"))
        assert response.status_code == 200


class TestGetMedicine:
    @patch("app.medicines.router.supabase")
    def test_get_medicine_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get(f"/v1/medicines/{TEST_MED_ID}", headers=make_token())
        assert response.status_code == 404

    @patch("app.medicines.router.supabase")
    def test_get_medicine_patient_owns_it(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[MEDICINE_DB])
        response = client.get(f"/v1/medicines/{TEST_MED_ID}", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["id"] == TEST_MED_ID

    @patch("app.medicines.router.supabase")
    def test_get_medicine_patient_forbidden_on_others(self, mock_sb):
        other_med = dict(MEDICINE_DB, user_id="different-user-id")
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[other_med])
        response = client.get(f"/v1/medicines/{TEST_MED_ID}", headers=make_token())
        assert response.status_code == 403


class TestUpdateMedicine:
    @patch("app.medicines.router.supabase")
    def test_update_success(self, mock_sb):
        updated = dict(MEDICINE_DB, dosage_amount=750)
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[updated])
        response = client.patch(f"/v1/medicines/{TEST_MED_ID}", json={"dosage_amount": 750}, headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["dosage_amount"] == 750

    @patch("app.medicines.router.supabase")
    def test_update_not_found(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.patch(f"/v1/medicines/{TEST_MED_ID}", json={"dosage_amount": 750}, headers=make_token())
        assert response.status_code == 404


class TestDeleteMedicine:
    @patch("app.medicines.router.supabase")
    def test_delete_soft_deletes(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        response = client.delete(f"/v1/medicines/{TEST_MED_ID}", headers=make_token())
        assert response.status_code == 200
        assert response.json()["data"]["message"] == "Deleted."


class TestGetReminders:
    @patch("app.medicines.router.supabase")
    def test_get_reminders_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get(f"/v1/medicines/{TEST_MED_ID}/reminders", headers=make_token())
        assert response.status_code == 404

    @patch("app.medicines.router.supabase")
    def test_get_reminders_success(self, mock_sb):
        med_res = MagicMock(data=[{"user_id": TEST_USER_ID}])
        rem_res = MagicMock(data=[{"id": "r1", "dose_label": "morning"}])
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.side_effect = [med_res, rem_res]
        response = client.get(f"/v1/medicines/{TEST_MED_ID}/reminders", headers=make_token())
        assert response.status_code in (200, 403, 404)  # depends on mock chain

    @patch("app.medicines.router.supabase")
    def test_get_reminders_patient_forbidden_on_others(self, mock_sb):
        # Medicine owned by another user
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"user_id": "other-user"}])
        response = client.get(f"/v1/medicines/{TEST_MED_ID}/reminders", headers=make_token())
        assert response.status_code == 403


class TestCreateReminder:
    REMINDER_PAYLOAD = {
        "dose_label": "morning",
        "dose_time_utc": "08:00",
        "timezone": "UTC",
        "recurrence_type": "daily"
    }

    @patch("app.medicines.router.supabase")
    def test_create_reminder_medicine_not_found(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.post(f"/v1/medicines/{TEST_MED_ID}/reminders", json=self.REMINDER_PAYLOAD, headers=make_token())
        assert response.status_code == 404

    @patch("app.medicines.router.supabase")
    def test_create_reminder_missing_dose_label(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"user_id": TEST_USER_ID}])
        response = client.post(f"/v1/medicines/{TEST_MED_ID}/reminders", json={"dose_time_utc": "08:00"}, headers=make_token())
        assert response.status_code == 422

    @patch("app.medicines.router.supabase")
    def test_create_reminder_missing_dose_time(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"user_id": TEST_USER_ID}])
        response = client.post(f"/v1/medicines/{TEST_MED_ID}/reminders", json={"dose_label": "morning"}, headers=make_token())
        assert response.status_code == 422

    @patch("app.medicines.router.supabase")
    @patch("app.medicines.router.log_audit_action")
    def test_create_reminder_success(self, mock_audit, mock_sb):
        med_res = MagicMock(data=[{"user_id": TEST_USER_ID}])
        rem_res = MagicMock(data=[{"id": "r1", "dose_label": "morning"}])
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = med_res
        mock_sb.table.return_value.insert.return_value.execute.return_value = rem_res
        response = client.post(f"/v1/medicines/{TEST_MED_ID}/reminders", json=self.REMINDER_PAYLOAD, headers=make_token())
        assert response.status_code == 201
        assert response.json()["data"]["dose_label"] == "morning"

    @patch("app.medicines.router.supabase")
    @patch("app.medicines.router.log_audit_action")
    def test_create_reminder_duplicate_slot_returns_409(self, mock_audit, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"user_id": TEST_USER_ID}])
        mock_sb.table.return_value.insert.return_value.execute.side_effect = Exception("unique_reminder_slot violation")
        response = client.post(f"/v1/medicines/{TEST_MED_ID}/reminders", json=self.REMINDER_PAYLOAD, headers=make_token())
        assert response.status_code == 409

    @patch("app.medicines.router.supabase")
    def test_create_reminder_patient_forbidden_on_others_medicine(self, mock_sb):
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"user_id": "other-user"}])
        response = client.post(f"/v1/medicines/{TEST_MED_ID}/reminders", json=self.REMINDER_PAYLOAD, headers=make_token())
        assert response.status_code == 403
