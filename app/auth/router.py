import logging
import base64
import hashlib
import json
import time
import io
try:
    import qrcode
    _QR_AVAILABLE = True
except ImportError:
    _QR_AVAILABLE = False
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from app.auth.schemas import UserRegister, UserLogin, ForgotPassword, ResetPassword, Token, MfaCode, MfaConfirm, RefreshRequest
from app.db.supabase import supabase, supabase_auth
from app.core.responses import SuccessResponse
from app.core.rate_limit import limiter
from app.services.audit import log_audit_action
from app.config import settings
from jose import jwt
import pyotp
from cryptography.fernet import Fernet
try:
    from gotrue.types import AdminUserAttributes
except ImportError:
    AdminUserAttributes = dict
from app.auth.dependencies import get_current_user

logger = logging.getLogger("adhera.auth")
router = APIRouter()

try:
    from gotrue.errors import AuthApiError
except ImportError:
    AuthApiError = Exception


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[dict])
@limiter.limit("10/minute")
async def register(request: Request, user_data: UserRegister):
    # Admin cannot self-register
    if user_data.role == "admin":
        raise HTTPException(status_code=403, detail="Admin accounts cannot be self-registered.")

    try:
        try:
            user_metadata = {
                "full_name": user_data.full_name,
                "role": user_data.role,
                "date_of_birth": user_data.date_of_birth.isoformat() if user_data.date_of_birth else None,
                "contact_number": user_data.contact_number,
                "timezone": user_data.timezone,
            }
            if user_data.role == "provider" and user_data.specialization:
                user_metadata["specialization"] = user_data.specialization

            res = supabase_auth.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": user_metadata
                },
            })
            if not res.user:
                raise Exception("Registration failed: user profile not created.")
        except AuthApiError as e:
            err_str = str(e).lower()
            if "already registered" in err_str or "user already registered" in err_str or "already exists" in err_str:
                return JSONResponse(
                    status_code=409,
                    content={"success": False, "error": {"code": "USER_EXISTS", "message": "An account with this email already exists. Please log in instead."}}
                )
            logger.error("Supabase sign_up AuthApiError: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error("Supabase sign_up failed: %s", str(e))
            raise HTTPException(status_code=400, detail=str(e))

        # Patient: auto-approved. Provider: pending approval.
        is_active = user_data.role == "patient"

        if supabase:
            try:
                profile_data = {
                    "id": res.user.id,
                    "full_name": user_data.full_name,
                    "role": user_data.role,
                    "date_of_birth": user_data.date_of_birth.isoformat() if user_data.date_of_birth else None,
                    "contact_number": user_data.contact_number,
                    "timezone": user_data.timezone,
                    "is_active": is_active,
                    "specialization": user_data.specialization if user_data.role == "provider" else None,
                }
                supabase.table("profiles").insert(profile_data).execute()
            except Exception as ex:
                logger.error(f"Failed to create profile: {repr(ex)}")

        try:
            log_audit_action("USER_REGISTERED", res.user.id, {"role": user_data.role, "is_active": is_active})
        except Exception as audit_err:
            logger.warning("Audit log failed for USER_REGISTERED: %s", audit_err)

        email_confirm_required = False
        if user_data.role == "patient" and (not hasattr(res, "session") or res.session is None):
            email_confirm_required = True

        if user_data.role == "provider":
            return SuccessResponse(data={"message": "Registration submitted. An admin will review your account within 24 hours.", "pending": True})
        if email_confirm_required:
            return SuccessResponse(data={"message": "Check your inbox to confirm your email.", "pending": False, "email_confirm_required": True})
        return SuccessResponse(data={"message": "Registration successful.", "pending": False})
    except HTTPException:
        raise
    except AuthApiError as e:
        err_str = str(e).lower()
        if "already registered" in err_str or "user already registered" in err_str or "already exists" in err_str:
            return JSONResponse(
                status_code=409,
                content={"success": False, "error": {"code": "USER_EXISTS", "message": "An account with this email already exists. Please log in instead."}}
            )
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=SuccessResponse[Token])
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    try:
        res = supabase_auth.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password,
        })
        if not res.session:
            log_audit_action("LOGIN_FAILED", None, {"email": credentials.email})
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # Check profile approval status
        if supabase:
            user_id = res.user.id if res.user else None
            if user_id:
                prof = supabase.table("profiles").select("role, is_active").eq("id", user_id).execute()
                if prof.data:
                    p = prof.data[0]
                    if p.get("role") == "provider" and not p.get("is_active", True):
                        raise HTTPException(
                            status_code=403,
                            detail={"code": "ACCOUNT_PENDING_APPROVAL", "message": "Your account is pending admin approval."}
                        )
                    if not p.get("is_active", True) and p.get("role") != "provider":
                        raise HTTPException(
                            status_code=403,
                            detail={"code": "ACCOUNT_DISABLED", "message": "Your account has been disabled."}
                        )

        # Check if MFA is enabled
        user_metadata = res.user.user_metadata or {}
        if user_metadata.get("mfa_enabled"):
            user_role = "patient"
            if supabase and res.user:
                prof = supabase.table("profiles").select("role").eq("id", res.user.id).execute()
                if prof.data:
                    val = prof.data[0].get("role", "patient")
                    if isinstance(val, str):
                        user_role = val

            # Generate encryption key derived from SUPABASE_JWT_SECRET
            key_bytes = hashlib.sha256(settings.SUPABASE_JWT_SECRET.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            cipher = Fernet(fernet_key)

            # Encrypt Supabase session tokens
            encrypted_session = cipher.encrypt(json.dumps({
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token
            }).encode()).decode()

            # Create partial token payload
            payload = {
                "sub": res.user.id,
                "role": user_role,
                "mfa_pending": True,
                "encrypted_session": encrypted_session,
                "exp": int(time.time()) + 300  # 5 minutes
            }
            partial_token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

            return SuccessResponse(data=Token(
                access_token="",
                refresh_token="",
                token_type="bearer",
                mfa_required=True,
                partial_token=partial_token
            ))

        return SuccessResponse(data=Token(
            access_token=res.session.access_token,
            refresh_token=res.session.refresh_token,
            token_type="bearer"
        ))
    except HTTPException:
        raise
    except AuthApiError as e:
        log_audit_action("LOGIN_FAILED", None, {"email": credentials.email, "reason": str(e)})
        raise HTTPException(status_code=401, detail="Invalid email or password.")

@router.post("/refresh", response_model=SuccessResponse[Token])
@limiter.limit("10/minute")
async def refresh(request: Request, body: RefreshRequest):
    try:
        res = supabase_auth.auth.refresh_session(refresh_token=body.refresh_token)
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        return SuccessResponse(data=Token(
            access_token=res.session.access_token,
            refresh_token=res.session.refresh_token,
            token_type="bearer"
        ))
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Failed to refresh token.")

@router.post("/logout", response_model=SuccessResponse[dict])
@limiter.limit("10/minute")
async def logout(request: Request):
    try:
        supabase_auth.auth.sign_out()
    except Exception:
        pass
    return SuccessResponse(data={"message": "Logged out."})

@router.post("/forgot-password", response_model=SuccessResponse[dict])
@router.post("/auth/forgot-password", response_model=SuccessResponse[dict])
@limiter.limit("3/hour")
async def forgot_password(request: Request, body: ForgotPassword):
    try:
        supabase_auth.auth.reset_password_for_email(
            body.email,
            options={"redirect_to": f"{settings.FRONTEND_URL}/reset-password.html"}
        )
    except Exception:
        pass
    return SuccessResponse(data={"message": "Reset link sent if email exists."})

@router.post("/reset-password", response_model=SuccessResponse[dict])
@limiter.limit("10/minute")
async def reset_password(request: Request, body: ResetPassword):
    try:
        res = supabase_auth.auth.update_user({"password": body.password})
        if not res.user:
            raise HTTPException(status_code=400, detail="Failed to reset password.")
        return SuccessResponse(data={"message": "Password updated."})
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify-email", response_model=SuccessResponse[dict])
async def verify_email(token: str):
    return SuccessResponse(data={"message": "Email verified handled by Supabase client implicitly."})

def get_mfa_cipher():
    # Use dedicated MFA_ENCRYPTION_KEY if set; fall back to deriving from JWT secret for backward compat
    if settings.MFA_ENCRYPTION_KEY:
        fernet_key = settings.MFA_ENCRYPTION_KEY.encode()
        # Ensure it's valid base64url 32-byte key
        if len(fernet_key) < 44:  # Fernet keys are 44 base64url chars
            key_bytes = hashlib.sha256(settings.MFA_ENCRYPTION_KEY.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key_bytes)
    else:
        key_bytes = hashlib.sha256(settings.SUPABASE_JWT_SECRET.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

@router.get("/mfa/status", response_model=SuccessResponse[dict])
async def mfa_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    res = supabase.table("profiles").select("mfa_secret").eq("id", user_id).execute()
    enabled = bool(res.data and res.data[0].get("mfa_secret"))
    return SuccessResponse(data={"mfa_enabled": enabled})

@router.post("/mfa/enable", response_model=SuccessResponse[dict])
async def mfa_enable(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        try:
            u = supabase.auth.admin.get_user_by_id(user_id)
            email = u.user.email
        except Exception:
            email = current_user.get("email") or current_user.get("user_metadata", {}).get("email", "user@adhera.app")

        # Generate TOTP secret and provisioning URI
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        qr_code_uri = totp.provisioning_uri(name=email, issuer_name="Adhera")

        # Encrypt secret and store it in profiles
        cipher = get_mfa_cipher()
        encrypted_secret = cipher.encrypt(secret.encode()).decode()

        supabase.table("profiles").update({"mfa_secret": encrypted_secret}).eq("id", user_id).execute()

        # Generate inline base64 QR image
        qr_base64 = None
        if _QR_AVAILABLE:
            try:
                qr = qrcode.make(qr_code_uri)
                buf = io.BytesIO()
                qr.save(buf, format="PNG")
                qr_base64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
            except Exception as qr_err:
                logger.warning(f"QR code generation error: {str(qr_err)}")

        log_audit_action("MFA_ENABLE_INITIATED", user_id, {})
        return SuccessResponse(data={
            "secret": secret,
            "qr_code_uri": qr_code_uri,
            "qr_code": qr_base64
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA enable error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"MFA setup failed: {str(e)}")

@router.post("/mfa/verify", response_model=SuccessResponse[dict])
async def mfa_verify(request: Request, body: MfaCode, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    res = supabase.table("profiles").select("mfa_secret").eq("id", user_id).execute()
    if not res.data or not res.data[0].get("mfa_secret"):
        raise HTTPException(status_code=400, detail="MFA has not been enabled/initiated for this user.")

    encrypted_secret = res.data[0]["mfa_secret"]
    cipher = get_mfa_cipher()
    try:
        secret = cipher.decrypt(encrypted_secret.encode()).decode()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt MFA secret.")

    totp = pyotp.TOTP(secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code.")

    # Activate MFA in user metadata
    supabase.auth.admin.update_user_by_id(
        user_id,
        AdminUserAttributes(user_metadata={"mfa_enabled": True})
    )

    log_audit_action("MFA_ACTIVATED", user_id, {})
    return SuccessResponse(data={"message": "MFA activated successfully."})

@router.post("/mfa/disable", response_model=SuccessResponse[dict])
async def mfa_disable(request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    # Clear secret in profiles and disable in metadata
    supabase.table("profiles").update({"mfa_secret": None}).eq("id", user_id).execute()

    supabase.auth.admin.update_user_by_id(
        user_id,
        AdminUserAttributes(user_metadata={"mfa_enabled": False})
    )

    log_audit_action("MFA_DISABLED", user_id, {})
    return SuccessResponse(data={"message": "MFA disabled successfully."})

@router.post("/mfa/confirm", response_model=SuccessResponse[Token])
async def mfa_confirm(request: Request, body: MfaConfirm):
    try:
        payload = jwt.decode(
            body.partial_token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"]
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired partial token.")

    if not payload.get("mfa_pending"):
        raise HTTPException(status_code=401, detail="Invalid partial token claim.")

    user_id = payload["sub"]

    res = supabase.table("profiles").select("mfa_secret").eq("id", user_id).execute()
    if not res.data or not res.data[0].get("mfa_secret"):
        raise HTTPException(status_code=400, detail="MFA is not set up for this user.")

    encrypted_secret = res.data[0]["mfa_secret"]
    cipher = get_mfa_cipher()
    try:
        secret = cipher.decrypt(encrypted_secret.encode()).decode()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt MFA secret.")

    totp = pyotp.TOTP(secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code.")

    try:
        session_data = json.loads(cipher.decrypt(payload["encrypted_session"].encode()).decode())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session data in token.")

    log_audit_action("MFA_LOGIN_SUCCESS", user_id, {})
    return SuccessResponse(data=Token(
        access_token=session_data["access_token"],
        refresh_token=session_data["refresh_token"],
        token_type="bearer"
    ))
