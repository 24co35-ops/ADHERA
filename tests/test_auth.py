import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
try:
    from gotrue.errors import AuthApiError
except ImportError:
    AuthApiError = Exception

client = TestClient(app)

@patch("app.auth.router.supabase")
def test_register_valid_patient(mock_supabase):
    mock_supabase.auth.sign_up.return_value = MagicMock(user=MagicMock(id="123"))
    response = client.post("/v1/auth/register", json={
        "email": "test@demo.com", "password": "Pass123!", "full_name": "Test", "role": "patient", "timezone": "UTC"
    })
    assert response.status_code == 201

@patch("app.auth.router.supabase")
def test_register_valid_provider(mock_supabase):
    mock_supabase.auth.sign_up.return_value = MagicMock(user=MagicMock(id="123"))
    response = client.post("/v1/auth/register", json={
        "email": "prov@demo.com", "password": "Pass123!", "full_name": "Prov", "role": "provider", "timezone": "UTC"
    })
    assert response.status_code == 201

@patch("app.auth.router.supabase")
def test_register_duplicate_email(mock_supabase):
    mock_supabase.auth.sign_up.side_effect = AuthApiError("User already registered", 400, "user_already_exists")
    response = client.post("/v1/auth/register", json={
        "email": "test@demo.com", "password": "Pass123!", "full_name": "Test", "role": "patient", "timezone": "UTC"
    })
    assert response.status_code in (400, 409)

def test_register_missing_fields():
    response = client.post("/v1/auth/register", json={"email": "test@demo.com"})
    assert response.status_code == 400

@patch("app.auth.router.supabase")
def test_login_valid(mock_supabase):
    mock_supabase.auth.sign_in_with_password.return_value = MagicMock(session=MagicMock(access_token="abc", refresh_token="def"))
    response = client.post("/v1/auth/login", json={"email": "test@demo.com", "password": "Pass123!"})
    assert response.status_code == 200
    assert response.json().get('data', response.json())["data"]["access_token"] == "abc"

@patch("app.auth.router.supabase")
def test_login_wrong_password(mock_supabase):
    mock_supabase.auth.sign_in_with_password.side_effect = AuthApiError("Invalid login credentials", 401, "invalid_credentials")
    response = client.post("/v1/auth/login", json={"email": "test@demo.com", "password": "wrong"})
    assert response.status_code == 401

@patch("app.auth.router.supabase")
def test_login_locked(mock_supabase):
    mock_supabase.auth.sign_in_with_password.side_effect = AuthApiError("Email rate limit exceeded", 429, "too_many_requests")
    response = client.post("/v1/auth/login", json={"email": "test@demo.com", "password": "wrong"})
    assert response.status_code in (401, 429)

@patch("app.auth.router.supabase")
def test_forgot_password_valid(mock_supabase):
    response = client.post("/v1/auth/forgot-password", json={"email": "test@demo.com"})
    assert response.status_code == 200

@patch("app.auth.router.supabase")
def test_forgot_password_unknown(mock_supabase):
    mock_supabase.auth.reset_password_email.side_effect = Exception("Unknown")
    response = client.post("/v1/auth/forgot-password", json={"email": "unknown@demo.com"})
    assert response.status_code == 200 # No enumeration
