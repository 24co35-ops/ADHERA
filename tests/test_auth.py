import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import base64
import hashlib
import json
import time
from jose import jwt
import pyotp
from cryptography.fernet import Fernet
from app.main import app
from app.config import settings

try:
    from gotrue.errors import AuthApiError
except ImportError:
    AuthApiError = Exception

def create_auth_api_error(message: str, status: int):
    try:
        return AuthApiError(message, status)
    except TypeError:
        try:
            return AuthApiError(message, status, "error_code")
        except TypeError:
            return AuthApiError(message)

client = TestClient(app)
app.state.limiter.enabled = False

# Use a valid UUID format for testing to prevent DB schema/audit log mismatch
TEST_USER_ID = "00000000-0000-0000-0000-000000000123"

def get_test_cipher():
    if settings.MFA_ENCRYPTION_KEY:
        fernet_key = settings.MFA_ENCRYPTION_KEY.encode()
        if len(fernet_key) < 44:
            key_bytes = hashlib.sha256(settings.MFA_ENCRYPTION_KEY.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key_bytes)
    else:
        key_bytes = hashlib.sha256(settings.SUPABASE_JWT_SECRET.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

def headers(role="patient", user_id=TEST_USER_ID, mfa_pending=None):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    if mfa_pending is not None:
        payload["mfa_pending"] = mfa_pending
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_register_valid_patient(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_up.return_value = MagicMock(user=MagicMock(id=TEST_USER_ID))
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])
    response = client.post("/v1/auth/register", json={
        "email": "test@demo.com", "password": "Pass123!", "full_name": "Test", "role": "patient", "timezone": "UTC"
    })
    assert response.status_code == 201

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_register_valid_provider(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_up.return_value = MagicMock(user=MagicMock(id=TEST_USER_ID))
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])
    response = client.post("/v1/auth/register", json={
        "email": "prov@demo.com", "password": "Pass123!", "full_name": "Prov", "role": "provider", "timezone": "UTC"
    })
    assert response.status_code == 201

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_register_duplicate_email(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_up.side_effect = create_auth_api_error("User already registered", 400)
    response = client.post("/v1/auth/register", json={
        "email": "test@demo.com", "password": "Pass123!", "full_name": "Test", "role": "patient", "timezone": "UTC"
    })
    assert response.status_code in (400, 409)

def test_register_missing_fields():
    response = client.post("/v1/auth/register", json={"email": "test@demo.com"})
    assert response.status_code == 400

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_login_valid(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_in_with_password.return_value = MagicMock(
        session=MagicMock(access_token="abc", refresh_token="def"),
        user=MagicMock(id=TEST_USER_ID, user_metadata={})
    )
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"role": "patient", "is_active": True}])
    response = client.post("/v1/auth/login", json={"email": "test@demo.com", "password": "Pass123!"})
    assert response.status_code == 200
    assert response.json().get('data', response.json())["access_token"] == "abc"

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_login_wrong_password(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_in_with_password.side_effect = create_auth_api_error("Invalid login credentials", 400)
    response = client.post("/v1/auth/login", json={"email": "test@demo.com", "password": "wrong"})
    assert response.status_code == 401

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_login_locked(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_in_with_password.side_effect = create_auth_api_error("Email rate limit exceeded", 429)
    response = client.post("/v1/auth/login", json={"email": "test@demo.com", "password": "wrong"})
    assert response.status_code in (401, 429)

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_forgot_password_valid(mock_supabase, mock_supabase_auth):
    response = client.post("/v1/auth/forgot-password", json={"email": "test@demo.com"})
    assert response.status_code == 200

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_forgot_password_unknown(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.reset_password_email.side_effect = Exception("Unknown")
    response = client.post("/v1/auth/forgot-password", json={"email": "unknown@demo.com"})
    assert response.status_code == 200

# --- MFA TESTS ---

def test_mfa_pending_token_rejection():
    # Attempt to access profile with an mfa_pending: true token
    response = client.get("/v1/profile/", headers=headers(mfa_pending=True))
    assert response.status_code == 401
    assert response.json().get("error", {}).get("message") == "MFA verification required"

@patch("app.auth.router.supabase")
def test_mfa_enable(mock_supabase):
    # Mock user details fetch and profile update
    mock_supabase.auth.admin.get_user_by_id.return_value = MagicMock(user=MagicMock(email="test@demo.com"))
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])

    response = client.post("/v1/auth/mfa/enable", headers=headers())
    assert response.status_code == 200
    res_data = response.json().get("data", {})
    assert "secret" in res_data
    assert "qr_code_uri" in res_data
    assert "otpauth://" in res_data["qr_code_uri"]

@patch("app.auth.router.supabase")
def test_mfa_verify_success(mock_supabase):
    # Generate a secret and valid TOTP code
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    cipher = get_test_cipher()
    encrypted_secret = cipher.encrypt(secret.encode()).decode()

    # Mock select mfa_secret and metadata update
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"mfa_secret": encrypted_secret}])
    mock_supabase.auth.admin.update_user_by_id.return_value = MagicMock()

    response = client.post("/v1/auth/mfa/verify", headers=headers(), json={"code": valid_code})
    assert response.status_code == 200
    assert response.json().get("data", {}).get("message") == "MFA activated successfully."

@patch("app.auth.router.supabase")
def test_mfa_verify_invalid(mock_supabase):
    secret = pyotp.random_base32()
    cipher = get_test_cipher()
    encrypted_secret = cipher.encrypt(secret.encode()).decode()

    # Mock select mfa_secret
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"mfa_secret": encrypted_secret}])

    response = client.post("/v1/auth/mfa/verify", headers=headers(), json={"code": "000000"})
    assert response.status_code == 400
    assert "Invalid MFA code" in response.json().get("error", {}).get("message")

@patch("app.auth.router.supabase")
def test_mfa_disable(mock_supabase):
    # Mock profiles update and admin metadata update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
    mock_supabase.auth.admin.update_user_by_id.return_value = MagicMock()

    response = client.post("/v1/auth/mfa/disable", headers=headers())
    assert response.status_code == 200
    assert response.json().get("data", {}).get("message") == "MFA disabled successfully."

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_login_with_mfa_enabled(mock_supabase, mock_supabase_auth):
    # Mock signIn to return a user with mfa_enabled user_metadata
    mock_supabase_auth.auth.sign_in_with_password.return_value = MagicMock(
        session=MagicMock(access_token="real_access", refresh_token="real_refresh"),
        user=MagicMock(id=TEST_USER_ID, user_metadata={"mfa_enabled": True})
    )
    # Mock profiles fetch for status check and role
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[{"role": "patient", "is_active": True}]),
        MagicMock(data=[{"role": "patient"}])
    ]

    response = client.post("/v1/auth/login", json={"email": "test@demo.com", "password": "Pass123!"})
    assert response.status_code == 200
    res_data = response.json().get("data", {})
    assert res_data["mfa_required"] is True
    assert "partial_token" in res_data
    assert res_data["access_token"] == ""

@patch("app.auth.router.supabase")
def test_mfa_confirm_success(mock_supabase):
    # Setup secret and session
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    cipher = get_test_cipher()
    encrypted_secret = cipher.encrypt(secret.encode()).decode()

    # Generate a partial token
    encrypted_session = cipher.encrypt(json.dumps({
        "access_token": "real_access_token",
        "refresh_token": "real_refresh_token"
    }).encode()).decode()

    payload = {
        "sub": TEST_USER_ID,
        "role": "patient",
        "mfa_pending": True,
        "encrypted_session": encrypted_session,
        "exp": int(time.time()) + 300
    }
    partial_token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

    # Mock DB query for profiles
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"mfa_secret": encrypted_secret}])

    response = client.post("/v1/auth/mfa/confirm", json={"partial_token": partial_token, "code": valid_code})
    assert response.status_code == 200
    res_data = response.json().get("data", {})
    assert res_data["access_token"] == "real_access_token"
    assert res_data["refresh_token"] == "real_refresh_token"


@patch("app.auth.router.supabase_auth")
def test_forgot_password_success(mock_supabase_auth):
    mock_supabase_auth.auth.reset_password_for_email.return_value = None
    response = client.post("/v1/auth/forgot-password", json={"email": "forgot@test.com"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "Reset link sent" in response.json()["data"]["message"]


@patch("app.auth.router.supabase_auth")
def test_auth_forgot_password_success(mock_supabase_auth):
    mock_supabase_auth.auth.reset_password_for_email.return_value = None
    response = client.post("/v1/auth/auth/forgot-password", json={"email": "forgot@test.com"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "Reset link sent" in response.json()["data"]["message"]


@patch("app.auth.router.supabase_auth")
def test_forgot_password_exception_handled(mock_supabase_auth):
    mock_supabase_auth.auth.reset_password_for_email.side_effect = Exception("Supabase error")
    response = client.post("/v1/auth/forgot-password", json={"email": "forgot@test.com"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "Reset link sent" in response.json()["data"]["message"]


