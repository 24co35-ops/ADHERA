import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("adhera.db")

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY: str | None = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET: str | None = os.environ.get("SUPABASE_JWT_SECRET")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError(
        "Missing required environment variables: SUPABASE_URL and SUPABASE_ANON_KEY must be set."
    )

if not SUPABASE_JWT_SECRET:
    raise ValueError(
        "Missing required environment variable: SUPABASE_JWT_SECRET must be set."
    )

# Public client — uses anon key, respects RLS
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client — uses service role key, bypasses RLS (only for admin operations)
supabase_admin: Client | None = (
    create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    if SUPABASE_SERVICE_ROLE_KEY
    else None
)

if not supabase_admin:
    logger.warning(
        "SUPABASE_SERVICE_ROLE_KEY not set — admin endpoints and CSV export will be unavailable."
    )
