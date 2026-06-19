import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
import jwt
from app.config import settings

client = TestClient(app)

def get_token(role="patient"):
    return jwt.encode({"aud": "authenticated", "sub": "user123", "user_metadata": {"role": role}}, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

def headers(role="patient"):
    return {"Authorization": f"Bearer {get_token(role)}"}

@patch("app.medicines.router.supabase")
def test_create_medicine_valid(mock_supabase):
    mock_supabase.table().insert().execute.return_value = type('obj', (object,), {'data': [{'id': '1'}]})()
    res = client.post("/v1/medicines/", headers=headers(), json={
        "name": "Med A", "dosage_amount": 10, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily", "start_date": "2025-01-01"
    })
    assert res.status_code == 201

def test_create_medicine_missing_field():
    res = client.post("/v1/medicines/", headers=headers(), json={"name": "Med A"})
    assert res.status_code == 400

@patch("app.medicines.router.supabase")
def test_create_medicine_prn(mock_supabase):
    mock_supabase.table().insert().execute.return_value = type('obj', (object,), {'data': [{'id': '1'}]})()
    res = client.post("/v1/medicines/", headers=headers(), json={
        "name": "Med PRN", "dosage_amount": 10, "dosage_unit": "mg", "route": "oral", "frequency_type": "prn", "start_date": "2025-01-01"
    })
    assert res.status_code == 201

@patch("app.medicines.router.supabase")
def test_update_medicine_valid(mock_supabase):
    mock_supabase.table().update().eq().eq().execute.return_value = type('obj', (object,), {'data': [{'id': '1'}]})()
    res = client.patch("/v1/medicines/1", headers=headers(), json={"dosage_amount": 20})
    assert res.status_code == 200

@patch("app.medicines.router.supabase")
def test_soft_delete_medicine(mock_supabase):
    mock_supabase.table().update().eq().eq().execute.return_value = type('obj', (object,), {'data': [{'id': '1'}]})()
    res = client.delete("/v1/medicines/1", headers=headers())
    assert res.status_code == 200
    mock_supabase.table().update.assert_called_with({"is_active": False})

# --- Advance Notify Reminder Tests ---

@patch("app.medicines.router.supabase")
def test_create_reminder_advance_notify_true(mock_supabase):
    mock_supabase.table().select().eq().execute.return_value = type('obj', (object,), {'data': [{'user_id': 'user123'}]})()
    mock_supabase.table().insert().execute.return_value = type('obj', (object,), {'data': [{'id': 'r1', 'advance_notify': True}]})()
    mock_supabase.table().select().eq().eq().eq().execute.return_value = type('obj', (object,), {'data': [{}]})()
    res = client.post("/v1/medicines/med1/reminders", headers=headers(), json={
        "dose_label": "Morning", "dose_time_utc": "08:00", "recurrence_type": "daily", "advance_notify": True
    })
    assert res.status_code == 201
    assert res.json()["data"]["advance_notify"] is True

@patch("app.medicines.router.supabase")
def test_create_reminder_advance_notify_default_false(mock_supabase):
    mock_supabase.table().select().eq().execute.return_value = type('obj', (object,), {'data': [{'user_id': 'user123'}]})()
    mock_supabase.table().insert().execute.return_value = type('obj', (object,), {'data': [{'id': 'r2', 'advance_notify': False}]})()
    mock_supabase.table().select().eq().eq().eq().execute.return_value = type('obj', (object,), {'data': [{}]})()
    res = client.post("/v1/medicines/med1/reminders", headers=headers(), json={
        "dose_label": "Night", "dose_time_utc": "21:00", "recurrence_type": "daily"
    })
    assert res.status_code == 201
    assert res.json()["data"]["advance_notify"] is False

@patch("app.reminders.router.supabase")
def test_patch_reminder_advance_notify(mock_supabase):
    mock_supabase.table().select().eq().execute.return_value = type('obj', (object,), {'data': [{'id': 'r1', 'user_id': 'user123', 'advance_notify': False}]})()
    mock_supabase.table().update().eq().execute.return_value = type('obj', (object,), {'data': [{'id': 'r1', 'advance_notify': True}]})()
    mock_supabase.table().select().eq().eq().eq().execute.return_value = type('obj', (object,), {'data': [{}]})()
    res = client.patch("/v1/reminders/r1", headers=headers(), json={"advance_notify": True})
    assert res.status_code == 200
    assert res.json()["data"]["advance_notify"] is True
