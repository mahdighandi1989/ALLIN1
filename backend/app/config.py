"""Application Configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets
import os
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Banking Operations"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Authentication - set to True to disable auth for development
    AUTH_DISABLED: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/banking"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False

    # JWT - Generate secure random key if not provided
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS - comma-separated list of allowed origins
    # Default to production origins only; add localhost in .env for local development
    CORS_ORIGINS: str = "https://banking-ops-frontend.onrender.com"

    # Security
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200

    # Session
    SESSION_TIMEOUT_MINUTES: int = 480  # 8 hours

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string.

        In production, automatically filters out localhost/127.0.0.1 origins
        to ensure security even if misconfigured.
        """
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

        # In production, filter out localhost origins for security
        if self.ENVIRONMENT.lower() == "production":
            filtered = [
                origin for origin in origins
                if "localhost" not in origin.lower() and "127.0.0.1" not in origin
            ]
            if len(filtered) < len(origins):
                import logging
                logging.getLogger(__name__).warning(
                    f"Filtered out localhost origins in production. "
                    f"Original: {origins}, Filtered: {filtered}"
                )
            return filtered

        return origins

    def model_post_init(self, __context) -> None:
        """Post-initialization validation and security checks"""
        # Generate secure SECRET_KEY if not provided
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(64)
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "SECRET_KEY environment variable must be explicitly set in production. "
                    "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )
        
        # Validate SECRET_KEY security in production
        # Note: Render's generateValue creates ~43-53 char keys which are still cryptographically secure (256+ bits)
        if self.ENVIRONMENT == "production":
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters long in production for security. "
                    "Use: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            
            # Check for common weak keys
            weak_keys = [
                "change-me-in-production",
                "your-secret-key",
                "secret",
                "password",
                "123456",
                "default-key"
            ]
            
            if self.SECRET_KEY.lower() in [key.lower() for key in weak_keys]:
                raise ValueError(
                    "SECRET_KEY appears to be a default/weak value. "
                    "Generate a cryptographically secure key for production."
                )
        
        # Validate database URL in production
        if self.ENVIRONMENT == "production":
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
                raise ValueError(
                    "DATABASE_URL must be set to a production database in production environment"
                )
        
        # Security validations
        if self.BCRYPT_ROUNDS < 10:
            raise ValueError("BCRYPT_ROUNDS must be at least 10 for security")
        
        if self.PASSWORD_MIN_LENGTH < 8:
            raise ValueError("PASSWORD_MIN_LENGTH must be at least 8 characters")
        
        if self.ACCESS_TOKEN_EXPIRE_MINUTES > 60 * 24 * 30:  # 30 days
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 30 days for security")

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() in ["development", "dev"]

    def get_database_config(self) -> dict:
        """Get database configuration dictionary"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_recycle": self.DATABASE_POOL_RECYCLE,
            "echo": self.DATABASE_ECHO and not self.is_production()
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()


# Security helper functions
def generate_secret_key() -> str:
    """Generate a cryptographically secure secret key"""
    return secrets.token_urlsafe(64)


def validate_environment_security() -> None:
    """Validate security configuration for current environment"""
    if settings.is_production():
        # Additional production security checks
        required_env_vars = ["SECRET_KEY", "DATABASE_URL"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(
                f"Required environment variables missing in production: {', '.join(missing_vars)}"
            )

        # CORS origins are automatically filtered in production by get_cors_origins()
        # Just ensure we have at least one valid origin
        cors_origins = settings.get_cors_origins()
        if not cors_origins:
            import logging
            logging.getLogger(__name__).warning(
                "No valid CORS origins configured for production. "
                "API requests from web browsers may be blocked."
            )


# Initialize security validation
try:
    validate_environment_security()
except ValueError as e:
    if settings.is_production():
        raise e
    else:
        # Log warning in development but don't fail
        import logging
        logging.getLogger(__name__).warning(f"Security validation warning: {e}")