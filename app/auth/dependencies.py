import json
import logging
import time

import httpx
import jwt as pyjwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt as jose_jwt
from jwt.algorithms import ECAlgorithm, RSAAlgorithm

from app.config import settings

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

_JWKS_URL = settings.SUPABASE_URL.rstrip("/") + "/auth/v1/.well-known/jwks.json"
_KEY_CACHE: dict[str, tuple] = {}  # kid -> (key_object, cached_at_timestamp)
_KEY_CACHE_TTL = 3600  # 1 hour


async def _get_signing_key(kid: str):
    """Retrieve signing key from in-memory cache or fetch dynamically via HTTPX."""
    if kid in _KEY_CACHE:
        cached_key, cached_at = _KEY_CACHE[kid]
        if time.time() - cached_at < _KEY_CACHE_TTL:
            return cached_key
        # TTL expired, remove and re-fetch
        del _KEY_CACHE[kid]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(_JWKS_URL, timeout=5.0)
            if resp.status_code == 200:
                jwks = resp.json()
                for key_dict in jwks.get("keys", []):
                    k = key_dict.get("kid")
                    kty = key_dict.get("kty")
                    if k and kty == "EC":
                        _KEY_CACHE[k] = (ECAlgorithm.from_jwk(json.dumps(key_dict)), time.time())
                    elif k and kty == "RSA":
                        _KEY_CACHE[k] = (RSAAlgorithm.from_jwk(json.dumps(key_dict)), time.time())
    except Exception as e:
        logger.warning("Failed to fetch JWKS from Supabase: %r", e)

    cached = _KEY_CACHE.get(kid)
    return cached[0] if cached else None


async def _decode_with_jwks(token: str, kid: str) -> dict:
    """Verify token using Supabase JWKS with local caching and clock leeway."""
    signing_key = await _get_signing_key(kid)
    if not signing_key:
        raise HTTPException(status_code=401, detail="Signing key not found")

    return pyjwt.decode(
        token,
        signing_key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        leeway=60,
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
            )
        else:
            # Production path: asymmetric JWKS verification with Supabase API fallback
            try:
                kid = header.get("kid", "")
                payload = await _decode_with_jwks(token, kid)
            except Exception as jwks_err:
                logger.info("JWKS verification missed, validating via Supabase Auth API: %r", jwks_err)
                from app.db.supabase import supabase_auth
                user_res = supabase_auth.auth.get_user(token)
                if not user_res or not user_res.user:
                    raise HTTPException(status_code=401, detail="Invalid token")
                u = user_res.user
                role = (
                    (u.app_metadata or {}).get("role")
                    or (u.user_metadata or {}).get("role")
                    or "patient"
                )
                return {
                    "user_id": u.id,
                    "role": role,
                }

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
    except pyjwt.ExpiredSignatureError as e:
        logger.info("JWT expired: %r", e)
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError as e:
        logger.warning("Invalid JWT: %r", e)
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        # Check for python-jose exceptions dynamically
        err_type = type(e).__name__
        if err_type == "ExpiredSignatureError":
            logger.info("JWT expired (jose): %r", e)
            raise HTTPException(status_code=401, detail="Token expired")
        elif err_type in ("JWTError", "JWTClaimsError", "SignatureError"):
            logger.warning("Invalid JWT (jose): %r", e)
            raise HTTPException(status_code=401, detail="Invalid token")
        logger.warning("JWT decode failed: %r", e)
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(*roles: str):
    async def dependency(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
