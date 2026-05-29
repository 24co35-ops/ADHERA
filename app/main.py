import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routers import auth, profile, medicines, reminders, doses, feedback, analytics, provider, admin

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("adhera")

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Adhera API starting up…")
    yield
    logger.info("Adhera API shutting down…")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Adhera API",
    description="Medication Adherence Platform API",
    version="1.0.0",
    # Hide docs in production
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Global exception handler — never leak stack traces to clients
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

# ---------------------------------------------------------------------------
# CORS — read allowed origins from env, support comma-separated list
# ---------------------------------------------------------------------------
_cors_env = os.getenv("CORS_ORIGIN", "http://localhost:3000,http://localhost:8000")
origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Health check (before routers so it is never shadowed by static mount)
# ---------------------------------------------------------------------------
@app.get("/v1/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# ---------------------------------------------------------------------------
# API Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router,      prefix="/v1/auth",      tags=["Authentication"])
app.include_router(profile.router,   prefix="/v1/profile",   tags=["Profile"])
app.include_router(medicines.router, prefix="/v1/medicines", tags=["Medicines"])
app.include_router(reminders.router, prefix="/v1/reminders", tags=["Reminders"])
app.include_router(doses.router,     prefix="/v1/doses",     tags=["Doses"])
app.include_router(feedback.router,  prefix="/v1/feedback",  tags=["Feedback"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
app.include_router(provider.router,  prefix="/v1/provider",  tags=["Provider"])
app.include_router(admin.router,     prefix="/v1/admin",     tags=["Admin"])

# ---------------------------------------------------------------------------
# Frontend static files (must be last — catch-all mount)
# ---------------------------------------------------------------------------
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
