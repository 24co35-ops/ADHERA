from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    # Optional: only needed for MFA partial tokens and local/test token generation.
    # Production JWT verification uses Supabase JWKS (asymmetric ES256).
    SUPABASE_JWT_SECRET: Optional[str] = ""
    # Separate key for encrypting MFA TOTP secrets. Generate with: python -c "import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
    MFA_ENCRYPTION_KEY: Optional[str] = ""  # Falls back to deriving from SUPABASE_JWT_SECRET if empty
    RESEND_API_KEY: str = ""
    CORS_ORIGIN: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"  # "production" enables strict CORS validation
    FRONTEND_URL: str = "https://adhera-seven.vercel.app"  # Used for password reset redirect URLs
    SENTRY_DSN: Optional[str] = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
