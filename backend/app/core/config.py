import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql+asyncpg://user:password@localhost/allin1_db"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_pool_recycle: int = 3600
    
    # Application settings
    app_name: str = "ALLIN1 Banking System"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()