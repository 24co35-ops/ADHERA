import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, profile, medicines, reminders, doses, feedback, analytics, provider, admin
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Adhera API",
    description="Medication Adherence Platform API",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
origins = [
    os.getenv("CORS_ORIGIN", "http://localhost:3000"),
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Health Check
@app.get("/v1/health")
async def health_check():
    return {"status": "healthy"}

# Include Routers
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/v1/profile", tags=["Profile"])
app.include_router(medicines.router, prefix="/v1/medicines", tags=["Medicines"])
app.include_router(reminders.router, prefix="/v1/reminders", tags=["Reminders"])
app.include_router(doses.router, prefix="/v1/doses", tags=["Doses"])
app.include_router(feedback.router, prefix="/v1/feedback", tags=["Feedback"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
app.include_router(provider.router, prefix="/v1/provider", tags=["Provider"])
app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])

# Serve Frontend Static Files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
