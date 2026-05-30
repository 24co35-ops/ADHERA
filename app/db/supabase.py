import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("adhera.db")

if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    raise ValueError(
        "Missing required environment variables: SUPABASE_URL and SUPABASE_ANON_KEY must be set."
    )

if not settings.SUPABASE_JWT_SECRET:
    raise ValueError(
        "Missing required environment variable: SUPABASE_JWT_SECRET must be set."
    )

SUPABASE_JWT_SECRET = settings.SUPABASE_JWT_SECRET

# Public client — uses anon key, respects RLS
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

# Admin client — uses service role key, bypasses RLS (only for admin operations)
supabase_admin: Client | None = (
    create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    if settings.SUPABASE_SERVICE_ROLE_KEY
    else None
)

if not supabase_admin:
    logger.warning(
        "SUPABASE_SERVICE_ROLE_KEY not set — admin endpoints and CSV export will be unavailable."
    )
