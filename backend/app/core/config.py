# File: backend/app/core/config.py

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # ... (بقیه تنظیمات بدون تغییر)

    # CORS settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,https://banking-ops-api.onrender.com", # <-- تغییر در این خط
        description="Comma-separated list of allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_max_age: int = Field(default=600, ge=0, le=86400)

    # ... (بقیه کد فایل بدون تغییر)