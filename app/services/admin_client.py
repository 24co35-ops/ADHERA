"""
================================================================================
ADMIN SUPABASE CLIENT (SERVICE-ROLE)
================================================================================
CRITICAL SECURITY WARNING:
This module initializes the service-role Supabase client which has full admin
privileges and bypasses PostgreSQL Row-Level Security (RLS) entirely.

NEVER import or use `admin_supabase` in patient, provider, or user-facing routes
(e.g., app/medicines, app/doses, app/feedback, app/provider, app/profile).
It is strictly reserved for:
1. `app/admin/router.py` (Identity directory & platform administration)
2. Dedicated system maintenance/audit scripts.
================================================================================
"""
import logging

import httpx

from app.config import settings
from supabase import Client, ClientOptions, create_client

logger = logging.getLogger("adhera.admin_client")

admin_supabase: Client | None = None

if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
    logger.warning("SUPABASE_SERVICE_ROLE_KEY is not configured; admin client operations will fail.")
else:
    transport = httpx.HTTPTransport(
        retries=3,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=5.0),
    )
    http_client = httpx.Client(transport=transport, timeout=15.0)
    opts = ClientOptions(postgrest_client_timeout=15.0, httpx_client=http_client)
    admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY, options=opts)

