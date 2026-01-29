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

    # JWT - Generate secure secret key if not provided
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: str = "https://banking-ops-frontend.onrender.com,http://localhost:3000,http://127.0.0.1:3000"

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Generate secure secret key if not provided via environment
        if not self.SECRET_KEY:
            # Check if we're in production (common production indicators)
            is_production = any([
                os.getenv('ENVIRONMENT') == 'production',
                os.getenv('ENV') == 'production',
                os.getenv('FLASK_ENV') == 'production',
                os.getenv('NODE_ENV') == 'production',
                not self.DEBUG,
                'render.com' in os.getenv('RENDER_EXTERNAL_URL', ''),
                os.getenv('RAILWAY_ENVIRONMENT') == 'production'
            ])
            
            if is_production:
                # In production, SECRET_KEY must be explicitly set
                raise ValueError(
                    "SECRET_KEY must be set in production environment. "
                    "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            else:
                # Development only: generate a warning and use a session key
                print("⚠️  WARNING: Using auto-generated SECRET_KEY for development. Set SECRET_KEY in .env for production!")
                self.SECRET_KEY = secrets.token_urlsafe(32)

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()