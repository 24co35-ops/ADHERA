from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import UserRegister, UserLogin, Token
from app.db.supabase import supabase, supabase_admin
from gotrue.errors import AuthApiError

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    try:
        # 1. Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name,
                    "role": user_data.role
                }
            }
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Registration failed")

        # 2. Create profile in public.profiles
        # This is often handled by a DB trigger in Supabase, but we'll do it explicitly here for clarity
        # if the trigger isn't set up yet.
        profile_data = {
            "id": auth_response.user.id,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "date_of_birth": user_data.date_of_birth.isoformat() if user_data.date_of_birth else None,
            "contact_number": user_data.contact_number,
            "timezone": user_data.timezone
        }
        
        # Use service role to bypass RLS for initial profile creation if needed
        # or just use the user's session if RLS allows.
        supabase_admin.table("profiles").insert(profile_data).execute()
        
        return {"message": "Registration successful. Please check your email for verification."}
        
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "token_type": "bearer"
        }
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout():
    supabase.auth.sign_out()
    return {"message": "Logged out successfully"}
