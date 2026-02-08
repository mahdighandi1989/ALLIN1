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
                        f"SECRET_KEY appears to be weak (contains '{pattern}'). "
                        "Use a cryptographically secure random string."
                    )
        return v

    @validator('cors_origins')
    def validate_cors_origins(cls, v):
        """Validate and convert CORS origins string to list"""
        if not v:
            return []
        origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        return origins

    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
