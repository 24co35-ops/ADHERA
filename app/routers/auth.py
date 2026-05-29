import os
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import UserRegister, UserLogin, Token
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

logger = logging.getLogger("adhera.auth")
router = APIRouter()

# Import gotrue error class safely
try:
    from gotrue.errors import AuthApiError
except ImportError:
    AuthApiError = Exception  # fallback


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new patient or provider account."""
    try:
        auth_response = supabase.auth.sign_up({
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

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Registration failed. Please try again.")

        return {"message": "Registration successful. Please check your email to verify your account."}

    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during registration")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during registration.")


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Authenticate and receive JWT tokens."""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password,
        })

        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer",
        }

    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during login")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during login.")


@router.post("/logout")
async def logout():
    """Sign out the current session (client-side token invalidation)."""
    try:
        supabase.auth.sign_out()
    except Exception:
        pass  # Best-effort; client should discard tokens regardless
    return {"message": "Logged out successfully."}


@router.get("/config")
async def get_config(user: dict = Depends(get_current_user)):
    """
    Return public Supabase client config for authenticated frontend clients.
    Requires a valid JWT so the anon key is not exposed to unauthenticated requests.
    """
    return {
        "supabase_url": os.environ.get("SUPABASE_URL"),
        "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY"),
    }
