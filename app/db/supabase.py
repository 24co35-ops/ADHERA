import logging
import os

from app.config import settings
from supabase import Client, create_client

logger = logging.getLogger("adhera.db")

if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    raise ValueError(
        "Missing required environment variables: SUPABASE_URL and SUPABASE_ANON_KEY must be set."
    )

SUPABASE_JWT_SECRET = settings.SUPABASE_JWT_SECRET or ""

# Public client — uses service role key if available, otherwise anon key to bypass RLS in backend
supabase: Client = (
    create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    if settings.SUPABASE_SERVICE_ROLE_KEY
    else create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
)

# Auth client — separate instance for sign_in/sign_up so it doesn't
# mutate the shared service-role client's Authorization header
supabase_auth: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

# ─────────────────────────────────────────────────────────────────────────────
# In-memory Auth User Cache (Prevents repeated slow GoTrue round-trips)
# ─────────────────────────────────────────────────────────────────────────────
import threading
import time

_AUTH_CACHE_LOCK = threading.Lock()
_AUTH_EMAIL_MAP: dict[str, str] = {}
_AUTH_SIGNIN_MAP: dict[str, str | None] = {}
_AUTH_CACHE_TIMESTAMP: float = 0.0
_AUTH_CACHE_TTL: float = 60.0  # 60 seconds


def clear_auth_users_cache() -> None:
    """Clear in-memory auth user cache (useful in tests)."""
    global _AUTH_EMAIL_MAP, _AUTH_SIGNIN_MAP, _AUTH_CACHE_TIMESTAMP
    with _AUTH_CACHE_LOCK:
        _AUTH_EMAIL_MAP = {}
        _AUTH_SIGNIN_MAP = {}
        _AUTH_CACHE_TIMESTAMP = 0.0


def get_auth_users_map(client: Client | None = None, force_refresh: bool = False) -> tuple[dict[str, str], dict[str, str | None]]:
    """
    Returns (email_map, last_sign_in_map) cached in memory for 60s.
    Prevents repetitive, slow GoTrue auth API HTTP calls across concurrent requests.
    """
    global _AUTH_EMAIL_MAP, _AUTH_SIGNIN_MAP, _AUTH_CACHE_TIMESTAMP
    is_test = os.environ.get("ENVIRONMENT") == "test" or getattr(settings, "ENVIRONMENT", "") == "test"
    now = time.time()

    sb = client if client is not None else supabase

    # If cache is valid and not in test mode and no custom mock client passed
    if not is_test and client is None and not force_refresh and (now - _AUTH_CACHE_TIMESTAMP) < _AUTH_CACHE_TTL and _AUTH_EMAIL_MAP:
        return _AUTH_EMAIL_MAP, _AUTH_SIGNIN_MAP

    with _AUTH_CACHE_LOCK:
        if not is_test and client is None and not force_refresh and (time.time() - _AUTH_CACHE_TIMESTAMP) < _AUTH_CACHE_TTL and _AUTH_EMAIL_MAP:
            return _AUTH_EMAIL_MAP, _AUTH_SIGNIN_MAP

        try:
            try:
                auth_res = sb.auth.admin.list_users(page=1, per_page=1000)
            except (TypeError, Exception):
                auth_res = sb.auth.admin.list_users()

            auth_users = getattr(auth_res, "users", auth_res) if not isinstance(auth_res, list) else auth_res
            if not isinstance(auth_users, list):
                auth_users = getattr(auth_users, "users", []) or []

            email_map: dict[str, str] = {}
            signin_map: dict[str, str | None] = {}
            for u in auth_users:
                uid = getattr(u, "id", None)
                if uid:
                    email_map[uid] = getattr(u, "email", "") or ""
                    signin_map[uid] = getattr(u, "last_sign_in_at", None)

            if not is_test and client is None:
                _AUTH_EMAIL_MAP = email_map
                _AUTH_SIGNIN_MAP = signin_map
                _AUTH_CACHE_TIMESTAMP = time.time()
            return email_map, signin_map
        except Exception as e:
            logger.warning("Failed to fetch/refresh auth users in get_auth_users_map: %s", e)
            if _AUTH_EMAIL_MAP:
                return _AUTH_EMAIL_MAP, _AUTH_SIGNIN_MAP
            return {}, {}


def get_auth_email(user_id: str, client: Client | None = None) -> str:
    """Helper to lookup email for a user_id from the cached auth users map."""
    email_map, _ = get_auth_users_map(client=client)
    return email_map.get(user_id, "")

