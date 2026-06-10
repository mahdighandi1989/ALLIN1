"""
Single Source of Truth for all application settings.
This file defines the configuration for the entire backend application,
loading values from environment variables and a .env file.
It includes robust validation to ensure security and correctness.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field, AliasChoices
import secrets
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database settings.
    # SECURITY / production note: the default DATABASE_URL below intentionally uses
    # placeholder "user:password" credentials and is for LOCAL DEV ONLY. Production
    # MUST override DATABASE_URL via the environment with real secret credentials —
    # validate_environment_security() / enforce_security_on_startup() flag the
    # insecure default when ENVIRONMENT=production so it can never be silently
    # shipped. See tests/test_config_security.py::test_production_config_defaults.
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

    # Telegram notifications (for critical-event alerts such as scan_failed).
    # When unset, notifications are logged instead of sent (graceful no-op).
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None)
    TELEGRAM_CHAT_ID: Optional[str] = Field(default=None)
    NOTIFY_RATE_LIMIT_SECONDS: int = Field(default=60, ge=0, le=3600)

    # Redis settings (for caching and sessions)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching"
    )
    REDIS_EXPIRE_SECONDS: int = Field(default=3600, ge=60, le=86400)

    # Monitoring and health checks
    HEALTH_CHECK_INTERVAL: int = Field(default=30, ge=10, le=300)
    METRICS_ENABLED: bool = Field(default=True)

    # Login/auth toggle. Login is ENFORCED by default (secure by default): every
    # request must carry a valid session. Set AUTH_DISABLED=true ONLY to
    # temporarily bypass login everywhere — protected endpoints then accept
    # requests without a JWT and operate as a shared "demo" admin, and the
    # frontend skips the login screen (it adapts at runtime via
    # GET /api/auth/config, no rebuild needed). Intended only as a local/dev
    # convenience; it must never be left on in production.
    AUTH_DISABLED: bool = Field(
        default=False,
        description="Bypass login/auth when True (dev only). Login is enforced by default.",
    )

    # Bootstrap admin account, created at startup if the users table is empty so
    # the app is loginable out of the box. Change these in any real deployment.
    DEFAULT_ADMIN_USERNAME: str = Field(default="admin")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="admin12345")
    DEFAULT_ADMIN_EMAIL: str = Field(default="admin@allin1.local")

    # ---- Google Sign-In (OAuth 2.0) + Drive backup ----
    # Set these in the deployment env (see docs). When GOOGLE_CLIENT_ID is empty
    # the Google endpoints return a clear "not configured" error instead of
    # crashing, so the rest of the app keeps working.
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(
        default="", description="Must match the Authorized redirect URI in Google Console"
    )
    # Emails that are always granted the admin role on Google sign-in (comma/space
    # separated). Everyone else signs in as 'pending' until an admin grants a role.
    ADMIN_EMAILS: str = Field(default="")
    # Where to send the browser after a successful Google login (the SPA reads the
    # token from the query string and stores it).
    POST_LOGIN_REDIRECT_PATH: str = Field(default="/auth/callback")
    # Drive backup destination + cadence.
    DRIVE_BACKUP_FOLDER: str = Field(default="BankingOps-Backups")
    BACKUP_DAILY_ENABLED: bool = Field(default=True)
    BACKUP_INTERVAL_HOURS: int = Field(default=24, ge=1, le=168)

    # ---- Google Drive sync (Service Account) ----
    # Automated, server-to-server Drive sync that does NOT depend on a user being
    # logged in. Everything the app pushes (DB snapshots, document attachments) is
    # written into GOOGLE_DRIVE_FOLDER_ID, organised into per-category/type
    # sub-folders with precise, traceable file names. To enable it:
    #   1. Create a Service Account in the Google Cloud console and download its
    #      JSON key; paste the WHOLE JSON (or its base64) into GOOGLE_CREDENTIALS_JSON.
    #   2. Create a destination folder in Google Drive, share it with the Service
    #      Account's client_email (Editor), and put the folder id in
    #      GOOGLE_DRIVE_FOLDER_ID.
    #   3. Set GOOGLE_DRIVE_ENABLED=true.
    # When disabled / unconfigured every sync call is a graceful no-op, so the rest
    # of the app keeps working unchanged.
    GOOGLE_DRIVE_ENABLED: bool = Field(default=False)
    GOOGLE_CREDENTIALS_JSON: str = Field(
        default="",
        description="Service Account key JSON (raw or base64) used to authenticate Drive sync",
    )
    GOOGLE_DRIVE_FOLDER_ID: str = Field(
        default="",
        description="Drive folder id (shared with the Service Account) that is the sync root",
    )
    # How often the background snapshot sync runs (reuses BACKUP_INTERVAL_HOURS).
    # The on-disk attachment uploads happen immediately, not on this cadence.
    DRIVE_SYNC_INTERVAL_HOURS: int = Field(default=24, ge=1, le=168)

    def google_drive_configured(self) -> bool:
        """True when Drive sync is switched on AND has the creds + folder it needs."""
        return bool(
            self.GOOGLE_DRIVE_ENABLED
            and self.GOOGLE_CREDENTIALS_JSON.strip()
            and self.GOOGLE_DRIVE_FOLDER_ID.strip()
        )

    def get_admin_emails(self) -> set[str]:
        """Lowercased set of always-admin emails parsed from ADMIN_EMAILS."""
        raw = (self.ADMIN_EMAILS or "").replace(",", " ")
        return {e.strip().lower() for e in raw.split() if e.strip()}

    def google_oauth_configured(self) -> bool:
        # GOOGLE_REDIRECT_URI is optional: when unset it is derived from the
        # incoming request (see app.routers.google_auth), so Google Sign-In works
        # out of the box with only the client id + secret configured.
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

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


def _is_insecure_default_database_url(database_url: Optional[str]) -> bool:
    """Return True when DATABASE_URL still carries the local-dev placeholder.

    The shipped default uses generic ``user:password`` credentials so the app is
    runnable out of the box for local development. Those credentials are an
    under-engineering / security risk if they survive into a non-local
    deployment, so this guard lets the startup validator flag the situation
    rather than silently connecting (or failing) with placeholder secrets.
    """
    if not database_url:
        return False
    return "user:password@" in database_url


def validate_environment_security(settings: Settings) -> List[str]:
    """Validate security settings and return warnings"""
    warnings = []

    if settings.ENVIRONMENT == 'production':
        if settings.DEBUG:
            warnings.append("Debug mode should be disabled in production")

        if settings.DOCS_URL or settings.REDOC_URL:
            warnings.append("API documentation endpoints should be disabled in production")

        # The default DATABASE_URL ships with placeholder "user:password"
        # credentials for local development. If that insecure default is still
        # in use under production it almost certainly means DATABASE_URL was not
        # overridden — a serious security risk — so surface it loudly.
        if _is_insecure_default_database_url(settings.DATABASE_URL):
            warnings.append(
                "DATABASE_URL still uses the insecure placeholder 'user:password' "
                "credentials in production — override DATABASE_URL via the "
                "environment with real, secret database credentials."
            )

    # TEMPORARY: AUTH_DISABLED bypasses the login requirement. Surface it loudly
    # so it is never forgotten — and especially never left on in production.
    if settings.AUTH_DISABLED:
        warnings.append(
            "AUTH_DISABLED is ON — login/authentication is BYPASSED and every "
            "request runs as the shared 'demo' user. This is intended only as a "
            "temporary convenience; set AUTH_DISABLED=false before any real use."
        )

    return warnings


def enforce_security_on_startup() -> None:
    """Run security validations at application startup.

    Logs all security warnings. AUTH_DISABLED is a supported (but strongly
    discouraged) temporary toggle, so it is surfaced as a prominent warning here
    rather than hard-failing — especially loud when left on in production.
    """
    for message in validate_environment_security(settings):
        logger.warning("SECURITY: %s", message)

    if settings.AUTH_DISABLED and settings.is_production():
        logger.error(
            "SECURITY: AUTH_DISABLED is ON in a PRODUCTION environment — the login "
            "requirement is bypassed for ALL requests. Set AUTH_DISABLED=false."
        )


# Create global settings instance
settings = get_settings()