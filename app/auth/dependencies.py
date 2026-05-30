import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

from jose import jwt, JWTError

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            audience="authenticated",
            options={"verify_signature": False}
        )
        return {
            "user_id": payload.get("sub"),
            "role": payload.get("user_metadata", {}).get("role", "patient")
        }
    except Exception as e:
        print("JWT DECODE ERROR:", repr(e))
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(*roles: str):
    async def dependency(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
