import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/allin1_db",
        description="Database connection URL"
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=30, ge=0, le=100)
    database_pool_recycle: int = Field(default=3600, ge=300, le=86400)
    database_echo: bool = Field(default=False, description="Enable SQL query logging")

    # Application settings
    app_name: str = Field(default="ALLIN1 Banking System", min_length=1)
    app_version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # Security settings - Critical security configurations
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(64),
        min_length=32,
        description="JWT signing key - must be cryptographically secure"
    )
    algorithm: str = Field(default="HS256", pattern="^(HS256|HS384|HS512|RS256|RS384|RS512)$")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    password_min_length: int = Field(default=8, ge=8, le=128)
    max_login_attempts: int = Field(default=5, ge=3, le=10)
    lockout_duration_minutes: int = Field(default=15, ge=5, le=60)

    # CORS settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_max_age: int = Field(default=600, ge=0, le=86400)

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, ge=10, le=1000)
    rate_limit_burst: int = Field(default=100, ge=20, le=2000)

    # Logging settings
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_max_bytes: int = Field(default=10485760, ge=1048576)  # 10MB
    log_backup_count: int = Field(default=5, ge=1, le=10)

    # API settings
    api_prefix: str = Field(default="/api", pattern="^/[a-zA-Z0-9/_-]*$")
    docs_url: Optional[str] = Field(default="/docs")
    redoc_url: Optional[str] = Field(default="/redoc")
    openapi_url: Optional[str] = Field(default="/openapi.json")

    # File upload settings
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    allowed_file_types: str = Field(
        default="pdf,doc,docx,xls,xlsx,png,jpg,jpeg",
        description="Comma-separated list of allowed file extensions"
    )

    # Email settings (for notifications)
    smtp_host: Optional[str] = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = Field(default=True)

    # Redis settings (for caching and sessions)
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching"
    )
    redis_expire_seconds: int = Field(default=3600, ge=60, le=86400)

    # Monitoring and health checks
    health_check_interval: int = Field(default=30, ge=10, le=300)
    metrics_enabled: bool = Field(default=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "forbid"  # Prevent unknown environment variables

    @validator('secret_key')
    def validate_secret_key(cls, v, values):
        """Validate secret key security requirements"""
        if not v or len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long for security. "
                "Use a cryptographically secure random string."
            )

        # Check for common weak patterns in production
        environment = values.get('environment', 'development')
        if environment == 'production':
            weak_patterns = [
                'change-me',
                'secret',
                'password',
                'your-secret-key',
                'development',
                'test',
                '123456',
                'default'
            ]
            v_lower = v.lower()
            for pattern in weak_patterns:
                if pattern in v_lower:
                    raise ValueError(
                        f"SECRET_KEY contains weak pattern '{pattern}'. "
                        "Use a cryptographically secure random string in production."
                    )

        return v

    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://', 'sqlite://', 'sqlite+aiosqlite://')):
            raise ValueError(
                "DATABASE_URL must start with postgresql://, postgresql+asyncpg://, "
                "sqlite://, or sqlite+aiosqlite://"
            )
        return v

    @validator('cors_origins')
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

    @validator('environment')
    def validate_environment_security(cls, v, values):
        """Validate security settings based on environment"""
        if v == 'production':
            # Additional production security checks
            debug = values.get('debug', False)
            if debug:
                logger.warning("Debug mode should be disabled in production")

            # Check if docs are exposed in production
            docs_url = values.get('docs_url')
            redoc_url = values.get('redoc_url')
            if docs_url or redoc_url:
                logger.warning(
                    "API documentation endpoints should be disabled in production "
                    "for security reasons"
                )

        return v

    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if not self.cors_origins:
            return []
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
        return self.cors_origins

    def get_allowed_file_types_list(self) -> List[str]:
        """Parse allowed file types from comma-separated string"""
        return [ext.strip().lower() for ext in self.allowed_file_types.split(',') if ext.strip()]

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == 'production'

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == 'development'

    def get_database_config(self) -> dict:
        """Get database configuration dictionary"""
        return {
            'url': self.database_url,
            'pool_size': self.database_pool_size,
            'max_overflow': self.database_max_overflow,
            'pool_recycle': self.database_pool_recycle,
            'echo': self.database_echo and self.debug
        }

    def get_security_headers(self) -> dict:
        """Get recommended security headers"""
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'",
        }

        if self.is_production():
            headers.update({
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'X-Permitted-Cross-Domain-Policies': 'none'
            })

        return headers

    def model_post_init(self, __context) -> None:
        """Post-initialization validation and warnings"""
        # Security warnings for production
        if self.is_production():
            if self.debug:
                logger.error("DEBUG mode is enabled in production - this is a security risk!")

            if 'localhost' in self.cors_origins or '127.0.0.1' in self.cors_origins:
                logger.warning("Localhost origins in CORS for production environment")

            if not self.database_url.startswith('postgresql'):
                logger.warning("Using non-PostgreSQL database in production")

        # Log configuration summary
        logger.info(f"Configuration loaded for environment: {self.environment}")
        logger.info(f"Debug mode: {self.debug}")
        logger.info(f"Database pool size: {self.database_pool_size}")
        logger.info(f"Token expiry: {self.access_token_expire_minutes} minutes")


# Global settings instance with lazy loading
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings instance with caching"""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise
    return _settings


# Convenience access to settings
settings = get_settings()


# Environment-specific configuration validation
def validate_production_config():
    """Validate configuration for production deployment"""
    issues = []

    if settings.debug:
        issues.append("Debug mode is enabled")

    if settings.secret_key and len(settings.secret_key) < 64:
        issues.append("SECRET_KEY should be at least 64 characters in production")

    if not settings.database_url.startswith('postgresql'):
        issues.append("Production should use PostgreSQL database")

    if settings.docs_url or settings.redoc_url:
        issues.append("API documentation should be disabled in production")

    if 'localhost' in settings.cors_origins:
        issues.append("CORS should not include localhost in production")

    if issues:
        raise ValueError(
            f"Production configuration issues found: {'; '.join(issues)}"
        )

    return True


# Export commonly used settings
__all__ = [
    'Settings',
    'settings',
    'get_settings',
    'validate_production_config'
]
