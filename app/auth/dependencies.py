import jwt as pyjwt
from jwt import PyJWKClient, PyJWKClientError
from jose import jwt as jose_jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

# JWKS client — keys cached for 1 hour; fetched lazily on first request
_JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwks_client = PyJWKClient(_JWKS_URL, cache_keys=True, lifespan=3600)


def _decode_with_jwks(token: str) -> dict:
    """Verify token using Supabase JWKS. Refreshes cache on key-not-found."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
    except PyJWKClientError:
        # Key ID not in cache — refresh once and retry
        _jwks_client.get_jwk_set(refresh=True)
        signing_key = _jwks_client.get_signing_key_from_jwt(token)

    return pyjwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Check algorithm without full verification to route appropriately
        header = pyjwt.get_unverified_header(token)
        alg = header.get("alg", "")

        if alg == "HS256" and settings.SUPABASE_JWT_SECRET:
            # HS256 path: MFA partial tokens and test-generated tokens
            payload = jose_jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": False},
            )
        else:
            # Production path: asymmetric JWKS verification (ES256 / RS256)
            payload = _decode_with_jwks(token)

        if payload.get("mfa_pending"):
            raise HTTPException(status_code=401, detail="MFA verification required")

        return {
            "user_id": payload.get("sub"),
            "role": (
                payload.get("app_metadata", {}).get("role")
                or payload.get("user_metadata", {}).get("role")
                or (payload.get("role") if payload.get("role") != "authenticated" else None)
                or "patient"
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        print("JWT DECODE ERROR:", repr(e))
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(*roles: str):
    async def dependency(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
