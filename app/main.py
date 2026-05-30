from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
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

app = FastAPI(title="Adhera API", version="1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGIN.split(",")] + ["http://localhost:8080", "https://*.vercel.app"],
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

app.include_router(auth_router, prefix="/v1/auth", tags=["auth"])
app.include_router(profile_router, prefix="/v1/profile", tags=["profile"])
app.include_router(medicines_router, prefix="/v1/medicines", tags=["medicines"])
app.include_router(doses_router, prefix="/v1/doses", tags=["doses"])
app.include_router(feedback_router, prefix="/v1/feedback", tags=["feedback"])
app.include_router(analytics_router, prefix="/v1/analytics", tags=["analytics"])
app.include_router(provider_router, prefix="/v1/provider", tags=["provider"])
app.include_router(admin_router, prefix="/v1/admin", tags=["admin"])
app.include_router(reminders_router, prefix="/v1/reminders", tags=["reminders"])

@app.get("/v1/health", response_model=SuccessResponse[dict])
async def health_check():
    return SuccessResponse(data={"status": "ok"})
