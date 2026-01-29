"""Application Configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Banking Operations"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/banking"

    # JWT - Use secure random key generation
    SECRET_KEY: str = os.getenv("SECRET_KEY") or secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: str = "https://banking-ops-frontend.onrender.com,http://localhost:3000,http://127.0.0.1:3000"

    class Config:
        env_file = ".env"

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def model_post_init(self, __context) -> None:
        """Post-initialization validation"""
        # Ensure SECRET_KEY is secure in production
        if not self.DEBUG and (not self.SECRET_KEY or self.SECRET_KEY == "change-me-in-production"):
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production environment. "
                "Set SECRET_KEY environment variable or update the configuration."
            )
        
        # Validate SECRET_KEY length for security
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long for security. "
                "Use a cryptographically secure random string."
            )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()