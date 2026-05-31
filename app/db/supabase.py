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

# Public client — uses service role key if available, otherwise anon key to bypass RLS in backend
supabase: Client = (
    create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    if settings.SUPABASE_SERVICE_ROLE_KEY
    else create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
)

# Admin client — alias of supabase
supabase_admin: Client = supabase

# Auth client — separate instance for sign_in/sign_up so it doesn't
# mutate the shared service-role client's Authorization header
supabase_auth: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

