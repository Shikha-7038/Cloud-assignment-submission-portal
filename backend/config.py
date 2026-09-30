"""
Central configuration.

Every secret / credential / URL is read from ENVIRONMENT VARIABLES (or a local
.env file that is git-ignored). Nothing sensitive is hardcoded in the source.
"""
import logging
import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root (never committed to Git)
logger = logging.getLogger("portal.config")

_PLACEHOLDERS = {"", "change-me", "change-me-to-a-long-random-string"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        raise RuntimeError(f"Environment variable {name} must be an integer")


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"                 # local | production
    cloud_provider: str = "local"          # local (emulator) | supabase (real cloud)
    database_url: str = "sqlite:///./data/portal.db"
    secret_key: str = ""
    access_token_expire_minutes: int = 60
    signed_url_expire_seconds: int = 300
    public_base_url: str = "http://localhost:8000"
    cors_origins: tuple = ("http://localhost:5173",)
    local_storage_dir: str = "./data/uploads"
    teacher_invite_code: str = ""
    auth_rate_limit_per_min: int = 10
    log_level: str = "INFO"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_bucket: str = "assignment-submissions"

    @classmethod
    def from_env(cls) -> "Settings":
        app_env = os.getenv("APP_ENV", "local").lower()
        provider = os.getenv("CLOUD_PROVIDER", "local").lower()
        if provider not in ("local", "supabase"):
            raise RuntimeError("CLOUD_PROVIDER must be 'local' or 'supabase'")

        secret = os.getenv("SECRET_KEY", "")
        if secret in _PLACEHOLDERS:
            if app_env == "production":
                raise RuntimeError("SECRET_KEY must be set to a long random value in production")
            secret = secrets.token_urlsafe(48)   # dev only: tokens reset on restart
            logger.warning("SECRET_KEY not set - generated a temporary one (dev only).")

        origins = tuple(o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip())

        settings = cls(
            app_env=app_env,
            cloud_provider=provider,
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data/portal.db"),
            secret_key=secret,
            access_token_expire_minutes=_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60),
            signed_url_expire_seconds=_int("SIGNED_URL_EXPIRE_SECONDS", 300),
            public_base_url=os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/"),
            cors_origins=origins,
            local_storage_dir=os.getenv("LOCAL_STORAGE_DIR", "./data/uploads"),
            teacher_invite_code=os.getenv("TEACHER_INVITE_CODE", ""),
            auth_rate_limit_per_min=_int("AUTH_RATE_LIMIT_PER_MIN", 10),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            supabase_url=os.getenv("SUPABASE_URL", "").rstrip("/"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            supabase_bucket=os.getenv("SUPABASE_BUCKET", "assignment-submissions"),
        )

        if provider == "supabase":
            missing = [n for n, v in {
                "SUPABASE_URL": settings.supabase_url,
                "SUPABASE_ANON_KEY": settings.supabase_anon_key,
                "SUPABASE_SERVICE_ROLE_KEY": settings.supabase_service_role_key,
            }.items() if not v]
            if missing:
                raise RuntimeError("Missing environment variables for Supabase: " + ", ".join(missing))
            if settings.database_url.startswith("sqlite"):
                raise RuntimeError("Set DATABASE_URL to your Supabase PostgreSQL connection string")
        return settings
