import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.auth.schemas import UserRegister, UserLogin, ForgotPassword, ResetPassword, Token
from app.db.supabase import supabase
from app.core.responses import SuccessResponse
from app.core.rate_limit import limiter
from app.services.audit import log_audit_action

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
        res = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name,
                    "role": user_data.role,
                    "date_of_birth": user_data.date_of_birth.isoformat() if user_data.date_of_birth else None,
                    "contact_number": user_data.contact_number,
                    "timezone": user_data.timezone,
                }
            },
        })
        if not res.user:
            raise HTTPException(status_code=400, detail="Registration failed.")

        # Patient: auto-approved. Provider: pending approval.
        is_active = user_data.role == "patient"

        if supabase:
            try:
                supabase.table("profiles").insert({
                    "id": res.user.id,
                    "full_name": user_data.full_name,
                    "role": user_data.role,
                    "date_of_birth": user_data.date_of_birth.isoformat() if user_data.date_of_birth else None,
                    "contact_number": user_data.contact_number,
                    "timezone": user_data.timezone,
                    "is_active": is_active,
                }).execute()
            except Exception as ex:
                print(f"Failed to create profile: {repr(ex)}")

        log_audit_action("USER_REGISTERED", res.user.id, {"role": user_data.role, "is_active": is_active})

        if user_data.role == "provider":
            return SuccessResponse(data={"message": "Registration submitted. An admin will review your account within 24 hours.", "pending": True})
        return SuccessResponse(data={"message": "Registration successful.", "pending": False})
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=SuccessResponse[Token])
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    try:
        res = supabase.auth.sign_in_with_password({
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

@router.post("/logout", response_model=SuccessResponse[dict])
@limiter.limit("10/minute")
async def logout(request: Request):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    return SuccessResponse(data={"message": "Logged out."})

@router.post("/forgot-password", response_model=SuccessResponse[dict])
@limiter.limit("3/hour")
async def forgot_password(request: Request, body: ForgotPassword):
    try:
        supabase.auth.reset_password_email(body.email)
    except Exception:
        pass
    return SuccessResponse(data={"message": "Reset link sent if email exists."})

@router.post("/reset-password", response_model=SuccessResponse[dict])
@limiter.limit("10/minute")
async def reset_password(request: Request, body: ResetPassword):
    try:
        res = supabase.auth.update_user({"password": body.password})
        if not res.user:
            raise HTTPException(status_code=400, detail="Failed to reset password.")
        return SuccessResponse(data={"message": "Password updated."})
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify-email", response_model=SuccessResponse[dict])
async def verify_email(token: str):
    return SuccessResponse(data={"message": "Email verified handled by Supabase client implicitly."})
