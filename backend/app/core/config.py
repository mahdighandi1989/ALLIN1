"""
Core Configuration Module
تنظیمات اصلی سیستم - قابل تنظیم از طریق پنل ادمین و متغیرهای محیطی
"""
from typing import List, Optional, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
import json


class Settings(BaseSettings):
    """تنظیمات اصلی برنامه"""

    # ================== App Settings ==================
    APP_NAME: str = "Banking Operations System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]

    # ================== Database Settings ==================
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/banking_ops"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis for caching and sessions
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # seconds

    # ================== Authentication ==================
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ================== AI Models Configuration ==================
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 4096

    # Anthropic Claude
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    ANTHROPIC_MAX_TOKENS: int = 4096

    # Google Gemini
    GOOGLE_AI_API_KEY: Optional[str] = None
    GOOGLE_AI_MODEL: str = "gemini-pro"

    # Default AI Provider
    DEFAULT_AI_PROVIDER: str = "openai"  # openai, anthropic, google

    # AI Features Configuration
    AI_ENABLED_FEATURES: List[str] = [
        "document_analysis",
        "risk_assessment",
        "data_extraction",
        "report_generation",
        "smart_suggestions"
    ]

    # ================== Google Drive Integration ==================
    GOOGLE_DRIVE_ENABLED: bool = True
    GOOGLE_CREDENTIALS_FILE: Optional[str] = None
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    GOOGLE_DRIVE_SYNC_INTERVAL: int = 300  # seconds

    # ================== Email Settings ==================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM_NAME: str = "Banking Operations System"
    EMAIL_FROM_ADDRESS: Optional[str] = None

    # ================== File Storage ==================
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".jpg", ".jpeg", ".png", ".gif",
        ".txt", ".csv"
    ]

    # ================== Business Rules ==================
    # Expiry Alert Days
    EXPIRY_ALERT_DAYS: int = 30
    EXPIRY_WARNING_DAYS: int = 60

    # Profile Completion Thresholds
    PROFILE_COMPLETION_MINIMUM: int = 70

    # KYC Settings
    KYC_VALIDITY_YEARS: int = 2

    # Facility Types
    FACILITY_TYPES: List[str] = [
        "OD",  # Overdraft
        "Loan",
        "ChqDisc",  # Cheque Discount
        "LG",  # Letter of Guarantee
        "TR",  # Trust Receipt
        "LC_Sight",
        "LC_Usance",
        "LoG"  # Loan on Gold
    ]

    # Document Types
    DOCUMENT_TYPES: List[str] = [
        "TradeLicense",
        "Passport",
        "EmiratesID",
        "Visa",
        "TenancyContract",
        "MOA",  # Memorandum of Association
        "BankStatement",
        "FinancialStatement"
    ]

    # ================== User Roles & Permissions ==================
    USER_ROLES: Dict[str, List[str]] = {
        "admin": ["*"],  # Full access
        "manager": [
            "read:all", "write:all", "delete:own",
            "manage:users", "view:reports", "export:data"
        ],
        "officer": [
            "read:all", "write:own", "delete:own",
            "view:reports"
        ],
        "viewer": [
            "read:all", "view:reports"
        ]
    }

    # ================== Rate Limiting ==================
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # ================== Logging ==================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or plain

    # ================== Render/Deployment ==================
    PORT: int = 8000
    WORKERS: int = 4

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [h.strip() for h in v.split(",")]
        return v

    @field_validator("AI_ENABLED_FEATURES", mode="before")
    @classmethod
    def parse_ai_features(cls, v):
        if isinstance(v, str):
            return [f.strip() for f in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DynamicSettings:
    """
    تنظیمات داینامیک قابل تغییر در Runtime
    این تنظیمات در دیتابیس ذخیره می‌شوند و از پنل ادمین قابل تغییر هستند
    """

    _instance = None
    _settings: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def load_from_db(self, db_session):
        """بارگذاری تنظیمات از دیتابیس"""
        from app.models.settings import SystemSetting

        settings = await db_session.execute(
            "SELECT key, value, value_type FROM system_settings WHERE is_active = true"
        )
        for row in settings:
            self._settings[row.key] = self._cast_value(row.value, row.value_type)

    def _cast_value(self, value: str, value_type: str) -> Any:
        """تبدیل مقدار به نوع مناسب"""
        if value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return value.lower() in ("true", "1", "yes")
        elif value_type == "json":
            return json.loads(value)
        elif value_type == "list":
            return [v.strip() for v in value.split(",")]
        return value

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    async def set(self, key: str, value: Any, db_session):
        """ذخیره تنظیم در دیتابیس"""
        self._settings[key] = value
        # Update in database
        # ...


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export
settings = get_settings()
dynamic_settings = DynamicSettings()
