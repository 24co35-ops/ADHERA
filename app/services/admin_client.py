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

from app.config import settings
from supabase import Client, create_client

logger = logging.getLogger("adhera.admin_client")

if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
    logger.warning("SUPABASE_SERVICE_ROLE_KEY is not configured; admin client operations will fail.")
    admin_supabase: Client = None
else:
    admin_supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
