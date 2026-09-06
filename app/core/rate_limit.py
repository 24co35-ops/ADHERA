import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Use Redis/Upstash backend if REDIS_URL is configured, otherwise fallback to in-memory
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"
if not settings.REDIS_URL:
    logging.getLogger("adhera.rate_limit").warning(
        "REDIS_URL not configured - rate limiting is per-process only (ineffective on serverless)"
    )
limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
