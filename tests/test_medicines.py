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
