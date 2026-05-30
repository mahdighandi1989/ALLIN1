"""
Single Source of Truth for all application settings.
This file defines the configuration for the entire backend application,
loading values from environment variables and a .env file.
It includes robust validation to ensure security and correctness.
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field, AliasChoices
import secrets
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost/allin1_db",
        description="Database connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=30, ge=0, le=100)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=300, le=86400)
    DATABASE_ECHO: bool = Field(default=False, description="Enable SQL query logging")

    # Application settings
    APP_NAME: str = Field(default="ALLIN1 Banking System", min_length=1)
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development")

    # Security settings - Critical security configurations
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(64),
        min_length=32,
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET_KEY"),
        description="JWT signing key - must be cryptographically secure "
                    "(read from env SECRET_KEY or JWT_SECRET_KEY)"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=8, le=128)
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, ge=3, le=10)
    LOCKOUT_DURATION_MINUTES: int = Field(default=15, ge=5, le=60)
    BCRYPT_ROUNDS: int = Field(default=12)

    # Brute-force protection for the login endpoint. After
    # LOGIN_RATE_LIMIT_PER_MINUTE failed attempts within a rolling minute the
    # endpoint returns HTTP 429; after ACCOUNT_LOCKOUT_THRESHOLD failed attempts
    # the account is locked for ACCOUNT_LOCKOUT_MINUTES (HTTP 423).
    LOGIN_RATE_LIMIT_PER_MINUTE: int = Field(default=5, ge=1, le=100)
    ACCOUNT_LOCKOUT_THRESHOLD: int = Field(default=10, ge=3, le=100)
    ACCOUNT_LOCKOUT_MINUTES: int = Field(default=30, ge=1, le=1440)

    # Force HTTPS / HSTS behaviour. Defaults to enabled in production.
    FORCE_HTTPS: Optional[bool] = Field(
        default=None,
        description="Redirect HTTP->HTTPS and emit HSTS. Defaults to True in production.",
    )

    # JWT Claims for token structure consistency
    JWT_ISSUER: str = "allin1-banking-system"
    JWT_AUDIENCE: str = "allin1-api-users"

    # CORS settings
    CORS_ORIGINS: str = Field(
        default="https://banking-ops-frontend.onrender.com,http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_MAX_AGE: int = Field(default=600, ge=0, le=86400)

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=10, le=1000)
    RATE_LIMIT_BURST: int = Field(default=100, ge=20, le=2000)

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    LOG_MAX_BYTES: int = Field(default=10485760, ge=1048576)  # 10MB
    LOG_BACKUP_COUNT: int = Field(default=5, ge=1, le=10)

    # API settings
    API_PREFIX: str = Field(default="/api")
    DOCS_URL: Optional[str] = Field(default="/docs")
    REDOC_URL: Optional[str] = Field(default="/redoc")
    OPENAPI_URL: Optional[str] = Field(default="/openapi.json")

    # File upload settings
    MAX_FILE_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_FILE_TYPES: str = Field(
        default="pdf,doc,docx,xls,xlsx,png,jpg,jpeg",
        description="Comma-separated list of allowed file extensions"
    )

    # Email settings (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = Field(default=True)

    # Redis settings (for caching and sessions)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching"
    )
    REDIS_EXPIRE_SECONDS: int = Field(default=3600, ge=60, le=86400)

    # Monitoring and health checks
    HEALTH_CHECK_INTERVAL: int = Field(default=30, ge=10, le=300)
    METRICS_ENABLED: bool = Field(default=True)

    # NOTE: The legacy AUTH_DISABLED setting has been removed. Authentication is
    # always enforced; there is no longer any way to disable it via configuration.
    # Any AUTH_DISABLED environment variable is ignored (extra="ignore").

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow unknown environment variables

    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        """Ensure DATABASE_URL uses async driver for SQLAlchemy async engine.
        Render.com and other providers supply postgresql:// but we need postgresql+asyncpg://"""
        if v and v.startswith('postgresql://'):
            v = v.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif v and v.startswith('postgres://'):
            v = v.replace('postgres://', 'postgresql+asyncpg://', 1)
        return v

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v, values):
        """Validate secret key security requirements.

        The key must be supplied via the environment (SECRET_KEY / JWT_SECRET_KEY)
        and must never be a weak or placeholder value. In production a weak key is
        a hard error; in development/test a secure ephemeral key is generated so
        local workflows keep working without shipping a hardcoded secret.
        """
        weak_placeholders = {
            "", "your-secret-key", "changeme", "change_me", "change-me",
            "change_me_in_production_use_openssl_rand_base64_32",
            "secret", "secret-key", "secretkey", "test", "password",
        }
        is_weak = (
            (not v)
            or (len(v) < 32)
            or (str(v).strip().lower() in weak_placeholders)
        )
        if is_weak:
            if str(values.get('ENVIRONMENT', '')).lower() == 'production':
                raise ValueError(
                    "SECRET_KEY (or JWT_SECRET_KEY) must be set to a strong, "
                    "non-default value of at least 32 characters in production. "
                    "Generate one with: openssl rand -base64 48"
                )
            # Development/test: generate a secure ephemeral key instead of
            # falling back to any hardcoded value.
            return secrets.token_urlsafe(64)
        return v

    @validator('ALGORITHM')
    def validate_algorithm(cls, v):
        """Reject the insecure 'none' algorithm and restrict to a safe allowlist."""
        if not v or str(v).strip().lower() in {"none", ""}:
            raise ValueError("JWT ALGORITHM must not be empty or 'none'")
        safe_algorithms = {
            "HS256", "HS384", "HS512",
            "RS256", "RS384", "RS512",
            "ES256", "ES384", "ES512",
            "PS256", "PS384", "PS512",
        }
        normalized = str(v).strip().upper()
        if normalized not in safe_algorithms:
            raise ValueError(
                f"Unsupported JWT ALGORITHM '{v}'. Allowed: {sorted(safe_algorithms)}"
            )
        return normalized

    @validator('CORS_ORIGINS')
    def validate_cors_origins(cls, v):
        """Validate CORS origins format"""
        if not v:
            return v

        origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        for origin in origins:
            if not (origin.startswith(('http://', 'https://')) or origin == '*'):
                raise ValueError(
                    f"Invalid CORS origin '{origin}'. "
                    "Origins must start with http:// or https://, or be '*'"
                )
        return v

    def get_cors_origins(self) -> List[str]:
        """Parse and return CORS origins, filtering localhost in production"""
        if not self.CORS_ORIGINS:
            return []

        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]

        if self.ENVIRONMENT == "production":
            filtered = [o for o in origins if 'localhost' not in o and '127.0.0.1' not in o]
            if len(filtered) < len(origins):
                logger.warning(
                    f"Filtered out localhost origins in production. "
                    f"Original: {origins}, Filtered: {filtered}"
                )
            return filtered

        return origins

    def get_cors_origins_list(self) -> List[str]:
        """Alias for get_cors_origins for compatibility"""
        return self.get_cors_origins()

    def get_allowed_file_types_list(self) -> List[str]:
        """Parse allowed file types from comma-separated string"""
        return [ext.strip().lower() for ext in self.ALLOWED_FILE_TYPES.split(',') if ext.strip()]

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == 'production'

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == 'development'

    def should_force_https(self) -> bool:
        """Whether HTTP should be redirected to HTTPS and HSTS emitted.

        Explicit FORCE_HTTPS wins; otherwise HTTPS is enforced in production.
        """
        if self.FORCE_HTTPS is not None:
            return self.FORCE_HTTPS
        return self.is_production()

    def get_database_config(self) -> dict:
        """Get database configuration dictionary"""
        return {
            'url': self.DATABASE_URL,
            'pool_size': self.DATABASE_POOL_SIZE,
            'max_overflow': self.DATABASE_MAX_OVERFLOW,
            'pool_recycle': self.DATABASE_POOL_RECYCLE,
            'echo': self.DATABASE_ECHO and self.DEBUG
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def generate_secret_key() -> str:
    """Generate a secure secret key"""
    return secrets.token_urlsafe(64)


def validate_environment_security(settings: Settings) -> List[str]:
    """Validate security settings and return warnings"""
    warnings = []

    if settings.ENVIRONMENT == 'production':
        if settings.DEBUG:
            warnings.append("Debug mode should be disabled in production")

        if settings.DOCS_URL or settings.REDOC_URL:
            warnings.append("API documentation endpoints should be disabled in production")

    # AUTH_DISABLED has been removed entirely — authentication is always enforced.
    # If a deprecated AUTH_DISABLED env var is still set, surface a warning so
    # operators remove it from their configuration.
    if os.getenv("AUTH_DISABLED"):
        warnings.append(
            "AUTH_DISABLED is set but has been removed and is now ignored — "
            "authentication is always enforced. Remove it from your environment."
        )

    return warnings


def enforce_security_on_startup() -> None:
    """Run security validations at application startup.

    Logs all security warnings and, as defense-in-depth, hard-fails in
    production if the removed AUTH_DISABLED flag is still set to a truthy value
    in the environment (so a stale insecure config cannot silently linger).
    """
    for message in validate_environment_security(settings):
        logger.warning("SECURITY: %s", message)

    auth_disabled_env = os.getenv("AUTH_DISABLED", "").strip().lower()
    if auth_disabled_env in {"1", "true", "yes", "on"} and settings.is_production():
        raise RuntimeError(
            "AUTH_DISABLED is set in a production environment. This flag has been "
            "removed and authentication can no longer be disabled. Remove "
            "AUTH_DISABLED from your environment to start the service."
        )


# Create global settings instance
settings = get_settings()