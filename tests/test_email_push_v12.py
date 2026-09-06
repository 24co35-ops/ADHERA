from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.main import app
from app.services.email import (
    get_confirmation_email_template,
    send_resend_email,
)

client = TestClient(app)
app.state.limiter.enabled = False

TEST_USER_ID = "00000000-0000-0000-0000-000000000123"

def headers(role="patient", user_id=TEST_USER_ID):
    payload = {
        "aud": "authenticated",
        "sub": user_id,
        "user_metadata": {"role": role}
    }
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


# ── 1. Email Service Tests ───────────────────────────────────────────────────

def test_confirmation_email_template_contains_branding_and_url():
    url = "https://adhera-seven.vercel.app/auth/confirm?token=xyz123"
    html = get_confirmation_email_template(url)
    assert "ADHERA" in html
    assert "#00dbe7" in html
    assert url in html
    assert "30 minutes" in html


@patch("app.services.email.httpx.AsyncClient.post")
async def test_send_resend_email_success(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    with patch("app.services.email.settings.RESEND_API_KEY", "re_test_key_123"):
        result = await send_resend_email(
            to="patient@test.com",
            subject="Test Subject",
            html="<p>Test</p>",
            user_id=TEST_USER_ID
        )
        assert result is True


async def test_send_resend_email_no_key_graceful():
    with patch("app.services.email.settings.RESEND_API_KEY", ""):
        result = await send_resend_email(
            to="patient@test.com",
            subject="Test Subject",
            html="<p>Test</p>"
        )
        assert result is False


# ── 2. Registration & Confirmation Flow Tests ─────────────────────────────────

@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_register_patient_creates_unconfirmed_state(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_up.return_value = MagicMock(user=MagicMock(id=TEST_USER_ID))
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

    response = client.post("/v1/auth/register", json={
        "email": "newpatient@test.com",
        "password": "Password123!",
        "full_name": "New Patient",
        "role": "patient",
        "timezone": "UTC"
    })
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["pending"] is True
    assert data["email_confirm_required"] is True
    assert "check your email" in data["message"].lower()


@patch("app.auth.router.supabase_auth")
@patch("app.auth.router.supabase")
def test_login_blocked_for_unconfirmed_patient(mock_supabase, mock_supabase_auth):
    mock_supabase_auth.auth.sign_in_with_password.return_value = MagicMock(
        session=MagicMock(access_token="abc", refresh_token="def"),
        user=MagicMock(id=TEST_USER_ID, user_metadata={"role": "patient"})
    )
    # Profile is inactive
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"role": "patient", "is_active": False}]
    )

    response = client.post("/v1/auth/login", json={
        "email": "unconfirmed@test.com",
        "password": "Password123!"
    })
    assert response.status_code == 403
    err = response.json().get("error") or response.json().get("detail")
    assert err["code"] == "EMAIL_NOT_CONFIRMED"


@patch("app.auth.router.supabase")
def test_confirm_email_success(mock_supabase):
    future_expiry = (datetime.now(timezone.utc) + timedelta(minutes=25)).isoformat()
    mock_record = {
        "id": "conf-uuid-1",
        "user_id": TEST_USER_ID,
        "email": "patient@test.com",
        "token": "valid_token_123",
        "expires_at": future_expiry,
        "used": False
    }

    # Mock select email_confirmations
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[mock_record]
    )
    # Mock update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])

    response = client.get("/v1/auth/confirm-email?token=valid_token_123")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "Email confirmed successfully" in response.json()["data"]["message"]


@patch("app.auth.router.supabase")
def test_confirm_email_expired_token(mock_supabase):
    past_expiry = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    mock_record = {
        "id": "conf-uuid-1",
        "user_id": TEST_USER_ID,
        "email": "patient@test.com",
        "token": "expired_token_123",
        "expires_at": past_expiry,
        "used": False
    }

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[mock_record]
    )

    response = client.get("/v1/auth/confirm-email?token=expired_token_123")
    assert response.status_code == 400
    err = response.json().get("error") or response.json().get("detail")
    assert err["code"] == "TOKEN_EXPIRED"


@patch("app.auth.router.supabase")
def test_confirm_email_already_used_token(mock_supabase):
    future_expiry = (datetime.now(timezone.utc) + timedelta(minutes=25)).isoformat()
    mock_record = {
        "id": "conf-uuid-1",
        "user_id": TEST_USER_ID,
        "email": "patient@test.com",
        "token": "used_token_123",
        "expires_at": future_expiry,
        "used": True
    }

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[mock_record]
    )

    response = client.get("/v1/auth/confirm-email?token=used_token_123")
    assert response.status_code == 400
    err = response.json().get("error") or response.json().get("detail")
    assert err["code"] == "INVALID_TOKEN"


@patch("app.auth.router.supabase")
def test_confirm_email_invalid_token(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )
    response = client.get("/v1/auth/confirm-email?token=non_existent")
    assert response.status_code == 400
    err = response.json().get("error") or response.json().get("detail")
    assert err["code"] == "INVALID_TOKEN"


@patch("app.auth.router.send_confirmation_email", new_callable=AsyncMock)
@patch("app.auth.router.supabase")
def test_resend_confirmation_success(mock_supabase, mock_send_email):
    mock_send_email.return_value = True

    # 1. ec_res query
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"user_id": TEST_USER_ID, "email": "patient@test.com", "used": False}]
    )
    # 2. prof query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"role": "patient", "is_active": False}]
    )
    # 3. update & insert
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])

    response = client.post("/v1/auth/resend-confirmation", json={"email": "patient@test.com"})
    assert response.status_code == 200
    assert response.json()["success"] is True


# ── 3. Push Subscription Persistence Tests ───────────────────────────────────

@patch("app.profile.router.supabase")
def test_save_push_subscription_with_json_and_columns(mock_supabase):
    saved_payload = None

    def capture_upsert(data, **kwargs):
        nonlocal saved_payload
        saved_payload = data
        mock_obj = MagicMock()
        mock_obj.execute.return_value = MagicMock(data=[{"id": "sub-123"}])
        return mock_obj

    mock_supabase.table.return_value.upsert.side_effect = capture_upsert

    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/token123",
        "keys": {
            "auth": "authKey456",
            "p256dh": "p256Key789"
        }
    }
    response = client.post("/v1/profile/push-subscription", headers=headers(), json=payload)
    assert response.status_code == 200
    assert saved_payload is not None
    assert saved_payload["endpoint"] == "https://fcm.googleapis.com/fcm/send/token123"
    assert saved_payload["auth"] == "authKey456"
    assert saved_payload["p256dh"] == "p256Key789"
    assert saved_payload["subscription"] == payload
