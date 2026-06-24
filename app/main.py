import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

sentry_sdk.init(
    dsn=os.environ.get(
        "SENTRY_DSN",
        "https://7fd9d1719a2c710684d1eea366210078@o4511619543465984.ingest.de.sentry.io/4511619570729040",
    ),
    integrations=[
        StarletteIntegration(),
        FastApiIntegration(),
    ],
    traces_sample_rate=0.2,
    profiles_sample_rate=0.1,
    environment=os.environ.get("ENVIRONMENT", "development"),
    send_default_pii=False,
    before_send=lambda event, hint: None if event.get("level") == "info" else event,
)

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.config import settings
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.core.exceptions import create_error_response, global_exception_handler
from app.auth.router import router as auth_router
from app.profile.router import router as profile_router
from app.medicines.router import router as medicines_router
from app.doses.router import router as doses_router
from app.feedback.router import router as feedback_router
from app.analytics.router import router as analytics_router
from app.provider.router import router as provider_router
from app.admin.router import router as admin_router
from app.reminders.router import router as reminders_router
from app.routers.assignments import router as assignments_router
from app.db.supabase import supabase

_DEV_LOCALHOST_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]

logger = logging.getLogger("adhera.main")
logging.basicConfig(level=logging.INFO, format="%(levelname)s     %(name)s - %(message)s")


def _get_cors_origins() -> list[str]:
    """Validate CORS_ORIGIN on startup; raise RuntimeError in production for unsafe values."""
    origin = (settings.CORS_ORIGIN or "").strip()
    env = settings.ENVIRONMENT.lower()

    if env == "production":
        if not origin or origin == "*":
            raise RuntimeError(
                "CORS_ORIGIN must be explicitly set to your frontend domain in production"
            )
        origins = [o.strip() for o in origin.split(",") if o.strip()]
        logger.info("CORS [production] allow_origins=%s", origins)
        return origins

    # Development: merge configured origin with localhost defaults
    configured = [o.strip() for o in origin.split(",") if o.strip()] if origin else []
    origins = list(dict.fromkeys(configured + _DEV_LOCALHOST_ORIGINS))  # deduplicated
    logger.info("CORS [%s] allow_origins=%s", env, origins)
    return origins


@asynccontextmanager
async def lifespan(app):
    _get_cors_origins()  # fail fast on bad config before accepting traffic
    yield


app = FastAPI(title="Adhera API", version="1.0", lifespan=lifespan)

app.state.limiter = limiter

async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Return ADHERA-shaped 429 instead of slowapi's default plain-text response."""
    return create_error_response(429, "RATE_LIMITED", "Too many requests")

app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        429: "RATE_LIMITED",
        503: "SERVICE_UNAVAILABLE"
    }
    code = code_map.get(exc.status_code, "SERVICE_UNAVAILABLE")
    return create_error_response(exc.status_code, code, str(exc.detail))

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return create_error_response(400, "VALIDATION_ERROR", "Validation failed", str(exc.errors()[0]['loc']))

app.add_exception_handler(Exception, global_exception_handler)

@app.get("/v1/health", response_model=SuccessResponse[dict])
async def health_check():
    db_status = "ok"
    try:
        supabase.table("profiles").select("id").limit(1).execute()
    except Exception:
        db_status = "error"
    return SuccessResponse(data={
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db": db_status
    })

app.include_router(auth_router, prefix="/v1/auth", tags=["auth"])
app.include_router(profile_router, prefix="/v1/profile", tags=["profile"])
app.include_router(medicines_router, prefix="/v1/medicines", tags=["medicines"])
app.include_router(doses_router, prefix="/v1/doses", tags=["doses"])
app.include_router(feedback_router, prefix="/v1/feedback", tags=["feedback"])
app.include_router(analytics_router, prefix="/v1/analytics", tags=["analytics"])
app.include_router(provider_router, prefix="/v1/provider", tags=["provider"])
app.include_router(admin_router, prefix="/v1/admin", tags=["admin"])
app.include_router(reminders_router, prefix="/v1/reminders", tags=["reminders"])
app.include_router(assignments_router, prefix="/v1")
