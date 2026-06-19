from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    # Optional: only needed for MFA partial tokens and local/test token generation.
    # Production JWT verification uses Supabase JWKS (asymmetric ES256).
    SUPABASE_JWT_SECRET: Optional[str] = ""
    RESEND_API_KEY: str = ""
    CORS_ORIGIN: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"  # "production" enables strict CORS validation

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
