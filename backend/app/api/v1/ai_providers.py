"""
AI Providers Management API
مدیریت پرووایدرهای هوش مصنوعی
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
import httpx
import json

from app.core.security import get_current_user, TokenData, require_role
from app.core.database import get_db
from app.models.settings import SystemSetting

router = APIRouter()


# ========== Schemas ==========
class AIProviderCreate(BaseModel):
    """Schema for creating a new AI provider"""
    provider_id: str = Field(..., description="Unique identifier (e.g., 'openai', 'anthropic')")
    name: str = Field(..., description="Display name")
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    enabled: bool = True
    provider_type: str = Field(default="openai_compatible", description="openai, anthropic, google, openai_compatible")


class AIProviderUpdate(BaseModel):
    """Schema for updating an AI provider"""
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    enabled: Optional[bool] = None


class AIProviderResponse(BaseModel):
    """Response schema for AI provider"""
    provider_id: str
    name: str
    enabled: bool
    has_api_key: bool
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    provider_type: str
    available_models: List[str] = []
    status: str = "unknown"  # connected, disconnected, error


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    name: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    pricing: Optional[Dict[str, Any]] = None


# ========== Known Provider Configurations ==========
KNOWN_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "provider_type": "openai",
        "models_endpoint": "/models",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "known_models": [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
            "gpt-3.5-turbo", "o1", "o1-mini", "o1-preview"
        ]
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "base_url": "https://api.anthropic.com/v1",
        "provider_type": "anthropic",
        "models_endpoint": "/models",
        "auth_header": "x-api-key",
        "auth_prefix": "",
        "known_models": [
            "claude-opus-4-20250514", "claude-sonnet-4-20250514",
            "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
        ]
    },
    "google": {
        "name": "Google (Gemini)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "provider_type": "google",
        "models_endpoint": "/models",
        "auth_header": None,  # Uses query param
        "auth_prefix": "",
        "known_models": [
            "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash",
            "gemini-pro", "gemini-pro-vision"
        ]
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "provider_type": "openai_compatible",
        "models_endpoint": "/models",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "known_models": [
            "llama-3.3-70b-versatile", "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant", "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "provider_type": "openai_compatible",
        "models_endpoint": "/models",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "known_models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "meta-llama/Llama-3.1-405B-Instruct-Turbo",
            "mistralai/Mixtral-8x22B-Instruct-v0.1",
            "Qwen/Qwen2.5-72B-Instruct-Turbo"
        ]
    },
    "mistral": {
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "provider_type": "openai_compatible",
        "models_endpoint": "/models",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "known_models": [
            "mistral-large-latest", "mistral-medium-latest",
            "mistral-small-latest", "open-mixtral-8x22b",
            "codestral-latest"
        ]
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "provider_type": "openai_compatible",
        "models_endpoint": "/models",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "known_models": [
            "deepseek-chat", "deepseek-coder", "deepseek-reasoner"
        ]
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "provider_type": "openai_compatible",
        "models_endpoint": "/models",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "known_models": []  # Dynamic from API
    },
    "ollama": {
        "name": "Ollama (Local)",
        "base_url": "http://localhost:11434/api",
        "provider_type": "ollama",
        "models_endpoint": "/tags",
        "auth_header": None,
        "auth_prefix": "",
        "known_models": []  # Dynamic from local instance
    }
}


# ========== Helper Functions ==========
def get_provider_setting_key(provider_id: str) -> str:
    """Generate setting key for provider"""
    return f"ai_provider_{provider_id}"


async def get_stored_providers(db: AsyncSession) -> Dict[str, Any]:
    """Get all stored AI providers from database"""
    result = await db.execute(
        select(SystemSetting).where(
            SystemSetting.key.like("ai_provider_%"),
            SystemSetting.is_active == True
        )
    )
    settings = result.scalars().all()

    providers = {}
    for setting in settings:
        provider_id = setting.key.replace("ai_provider_", "")
        try:
            providers[provider_id] = json.loads(setting.value) if setting.value else {}
        except json.JSONDecodeError:
            providers[provider_id] = {}

    return providers


async def save_provider_setting(db: AsyncSession, provider_id: str, data: Dict[str, Any]):
    """Save provider settings to database"""
    key = get_provider_setting_key(provider_id)

    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = json.dumps(data)
        setting.value_type = "json"
    else:
        setting = SystemSetting(
            key=key,
            value=json.dumps(data),
            value_type="json",
            category="ai",
            label=f"AI Provider: {data.get('name', provider_id)}",
            is_encrypted=True  # API keys should be encrypted
        )
        db.add(setting)

    await db.commit()


async def fetch_models_from_api(provider_config: Dict[str, Any], api_key: str) -> List[str]:
    """Fetch available models from provider API"""
    provider_type = provider_config.get("provider_type", "openai_compatible")
    base_url = provider_config.get("base_url", "")
    models_endpoint = provider_config.get("models_endpoint", "/models")

    if not api_key and provider_type != "ollama":
        return provider_config.get("known_models", [])

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            params = {}

            # Set auth header based on provider type
            auth_header = provider_config.get("auth_header")
            if auth_header:
                auth_prefix = provider_config.get("auth_prefix", "")
                headers[auth_header] = f"{auth_prefix}{api_key}"

            # Google uses query param for auth
            if provider_type == "google":
                params["key"] = api_key

            # Add anthropic-specific headers
            if provider_type == "anthropic":
                headers["anthropic-version"] = "2023-06-01"

            url = f"{base_url}{models_endpoint}"
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()

                # Parse response based on provider type
                if provider_type == "openai" or provider_type == "openai_compatible":
                    models = data.get("data", [])
                    # Filter to only chat/completion models
                    model_ids = []
                    for m in models:
                        model_id = m.get("id", "")
                        # Filter out embedding, whisper, dall-e, tts models
                        if not any(x in model_id.lower() for x in ["embedding", "whisper", "dall-e", "tts", "moderation"]):
                            model_ids.append(model_id)
                    return sorted(model_ids)

                elif provider_type == "anthropic":
                    models = data.get("data", [])
                    return [m.get("id", "") for m in models if m.get("id")]

                elif provider_type == "google":
                    models = data.get("models", [])
                    return [m.get("name", "").replace("models/", "") for m in models
                            if "generateContent" in m.get("supportedGenerationMethods", [])]

                elif provider_type == "ollama":
                    models = data.get("models", [])
                    return [m.get("name", "") for m in models]

            # Fallback to known models
            return provider_config.get("known_models", [])

    except Exception as e:
        print(f"Error fetching models: {e}")
        return provider_config.get("known_models", [])


async def test_provider_connection(provider_config: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """Test connection to AI provider"""
    provider_type = provider_config.get("provider_type", "openai_compatible")
    base_url = provider_config.get("base_url", "")

    if not api_key and provider_type != "ollama":
        return {"status": "disconnected", "message": "No API key provided"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            params = {}

            auth_header = provider_config.get("auth_header")
            if auth_header:
                auth_prefix = provider_config.get("auth_prefix", "")
                headers[auth_header] = f"{auth_prefix}{api_key}"

            if provider_type == "google":
                params["key"] = api_key

            if provider_type == "anthropic":
                headers["anthropic-version"] = "2023-06-01"

            # Use models endpoint to test
            models_endpoint = provider_config.get("models_endpoint", "/models")
            url = f"{base_url}{models_endpoint}"

            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return {"status": "connected", "message": "Connection successful"}
            elif response.status_code == 401:
                return {"status": "error", "message": "Invalid API key"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Access forbidden - check API key permissions"}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}

    except httpx.TimeoutException:
        return {"status": "error", "message": "Connection timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ========== API Endpoints ==========
@router.get("/providers", response_model=List[AIProviderResponse])
async def list_ai_providers(
    current_user: TokenData = Depends(require_role(["admin", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    لیست همه پرووایدرهای AI پیکربندی شده
    """
    stored_providers = await get_stored_providers(db)

    providers = []

    # Add known providers
    for provider_id, config in KNOWN_PROVIDERS.items():
        stored = stored_providers.get(provider_id, {})
        api_key = stored.get("api_key", "")

        providers.append(AIProviderResponse(
            provider_id=provider_id,
            name=config["name"],
            enabled=stored.get("enabled", False),
            has_api_key=bool(api_key),
            base_url=stored.get("base_url") or config.get("base_url"),
            default_model=stored.get("default_model"),
            provider_type=config["provider_type"],
            available_models=config.get("known_models", []),
            status="unknown"
        ))

    # Add custom providers
    for provider_id, stored in stored_providers.items():
        if provider_id not in KNOWN_PROVIDERS:
            providers.append(AIProviderResponse(
                provider_id=provider_id,
                name=stored.get("name", provider_id),
                enabled=stored.get("enabled", False),
                has_api_key=bool(stored.get("api_key")),
                base_url=stored.get("base_url"),
                default_model=stored.get("default_model"),
                provider_type=stored.get("provider_type", "openai_compatible"),
                available_models=[],
                status="unknown"
            ))

    return providers


@router.get("/providers/known")
async def list_known_providers(
    current_user: TokenData = Depends(get_current_user)
):
    """
    لیست پرووایدرهای شناخته شده (برای انتخاب سریع)
    """
    return {
        "providers": [
            {
                "id": pid,
                "name": config["name"],
                "provider_type": config["provider_type"],
                "default_base_url": config["base_url"],
                "known_models": config.get("known_models", [])
            }
            for pid, config in KNOWN_PROVIDERS.items()
        ]
    }


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: str,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت جزئیات یک پرووایدر
    """
    stored_providers = await get_stored_providers(db)
    stored = stored_providers.get(provider_id, {})
    config = KNOWN_PROVIDERS.get(provider_id, {})

    if not stored and not config:
        raise HTTPException(status_code=404, detail="Provider not found")

    return {
        "provider_id": provider_id,
        "name": stored.get("name") or config.get("name", provider_id),
        "enabled": stored.get("enabled", False),
        "has_api_key": bool(stored.get("api_key")),
        "base_url": stored.get("base_url") or config.get("base_url"),
        "default_model": stored.get("default_model"),
        "provider_type": stored.get("provider_type") or config.get("provider_type", "openai_compatible"),
        "known_models": config.get("known_models", [])
    }


@router.post("/providers")
async def create_provider(
    provider: AIProviderCreate,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد پرووایدر AI جدید (کاستوم)
    """
    # Check if already exists - but allow updating known providers that don't have data yet
    stored_providers = await get_stored_providers(db)
    if provider.provider_id in stored_providers:
        raise HTTPException(status_code=400, detail="Provider ID already exists. Use PUT to update.")

    data = {
        "name": provider.name,
        "api_key": provider.api_key,
        "base_url": provider.base_url,
        "default_model": provider.default_model,
        "enabled": provider.enabled,
        "provider_type": provider.provider_type
    }

    await save_provider_setting(db, provider.provider_id, data)

    # Refresh AI service cache so new keys are available immediately
    from app.services.ai_service import ai_service
    ai_service.refresh_providers()

    return {
        "message": "Provider created successfully",
        "provider_id": provider.provider_id
    }


@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    update: AIProviderUpdate,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی تنظیمات پرووایدر
    """
    stored_providers = await get_stored_providers(db)
    existing = stored_providers.get(provider_id, {})
    config = KNOWN_PROVIDERS.get(provider_id, {})

    # Merge with existing
    data = {
        "name": update.name if update.name is not None else (existing.get("name") or config.get("name", provider_id)),
        "api_key": update.api_key if update.api_key is not None else existing.get("api_key"),
        "base_url": update.base_url if update.base_url is not None else existing.get("base_url"),
        "default_model": update.default_model if update.default_model is not None else existing.get("default_model"),
        "enabled": update.enabled if update.enabled is not None else existing.get("enabled", False),
        "provider_type": existing.get("provider_type") or config.get("provider_type", "openai_compatible")
    }

    await save_provider_setting(db, provider_id, data)

    # Refresh AI service cache so new keys are available immediately
    from app.services.ai_service import ai_service
    ai_service.refresh_providers()

    return {
        "message": "Provider updated successfully",
        "provider_id": provider_id
    }


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف پرووایدر کاستوم
    """
    if provider_id in KNOWN_PROVIDERS:
        # Just disable and remove API key for known providers
        await save_provider_setting(db, provider_id, {"enabled": False, "api_key": None})
        return {"message": "Provider disabled"}

    key = get_provider_setting_key(provider_id)
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.is_active = False
        await db.commit()

    return {"message": "Provider deleted successfully"}


@router.post("/providers/{provider_id}/test")
async def test_provider(
    provider_id: str,
    api_key: Optional[str] = None,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    تست اتصال به پرووایدر
    """
    stored_providers = await get_stored_providers(db)
    stored = stored_providers.get(provider_id, {})
    config = KNOWN_PROVIDERS.get(provider_id, {})

    if not config and not stored:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Use provided API key or stored one
    test_key = api_key or stored.get("api_key", "")

    # Merge config
    provider_config = {
        "base_url": stored.get("base_url") or config.get("base_url"),
        "provider_type": stored.get("provider_type") or config.get("provider_type", "openai_compatible"),
        "models_endpoint": config.get("models_endpoint", "/models"),
        "auth_header": config.get("auth_header", "Authorization"),
        "auth_prefix": config.get("auth_prefix", "Bearer ")
    }

    result = await test_provider_connection(provider_config, test_key)
    return result


@router.get("/providers/{provider_id}/models")
async def get_provider_models(
    provider_id: str,
    refresh: bool = False,
    current_user: TokenData = Depends(require_role(["admin", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت لیست مدل‌های موجود از پرووایدر
    اگر refresh=true باشد، از API پرووایدر می‌گیره
    """
    stored_providers = await get_stored_providers(db)
    stored = stored_providers.get(provider_id, {})
    config = KNOWN_PROVIDERS.get(provider_id, {})

    if not config and not stored:
        raise HTTPException(status_code=404, detail="Provider not found")

    api_key = stored.get("api_key", "")

    # Merge config
    provider_config = {
        "base_url": stored.get("base_url") or config.get("base_url"),
        "provider_type": stored.get("provider_type") or config.get("provider_type", "openai_compatible"),
        "models_endpoint": config.get("models_endpoint", "/models"),
        "auth_header": config.get("auth_header", "Authorization"),
        "auth_prefix": config.get("auth_prefix", "Bearer "),
        "known_models": config.get("known_models", [])
    }

    if refresh and api_key:
        models = await fetch_models_from_api(provider_config, api_key)
    else:
        models = config.get("known_models", [])

    return {
        "provider_id": provider_id,
        "models": models,
        "refreshed": refresh and bool(api_key)
    }


@router.post("/providers/{provider_id}/fetch-models")
async def fetch_models(
    provider_id: str,
    api_key: Optional[str] = None,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت و ذخیره مدل‌های موجود از API پرووایدر
    """
    stored_providers = await get_stored_providers(db)
    stored = stored_providers.get(provider_id, {})
    config = KNOWN_PROVIDERS.get(provider_id, {})

    if not config and not stored:
        raise HTTPException(status_code=404, detail="Provider not found")

    test_key = api_key or stored.get("api_key", "")

    provider_config = {
        "base_url": stored.get("base_url") or config.get("base_url"),
        "provider_type": stored.get("provider_type") or config.get("provider_type", "openai_compatible"),
        "models_endpoint": config.get("models_endpoint", "/models"),
        "auth_header": config.get("auth_header", "Authorization"),
        "auth_prefix": config.get("auth_prefix", "Bearer "),
        "known_models": config.get("known_models", [])
    }

    models = await fetch_models_from_api(provider_config, test_key)

    return {
        "provider_id": provider_id,
        "models": models,
        "count": len(models)
    }


@router.get("/default-provider")
async def get_default_provider(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت پرووایدر پیش‌فرض
    """
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "default_ai_provider")
    )
    setting = result.scalar_one_or_none()

    return {
        "provider_id": setting.value if setting else "openai",
        "available": list(KNOWN_PROVIDERS.keys())
    }


@router.put("/default-provider/{provider_id}")
async def set_default_provider(
    provider_id: str,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    تنظیم پرووایدر پیش‌فرض
    """
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "default_ai_provider")
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = provider_id
    else:
        setting = SystemSetting(
            key="default_ai_provider",
            value=provider_id,
            value_type="string",
            category="ai",
            label="Default AI Provider"
        )
        db.add(setting)

    await db.commit()

    return {
        "message": "Default provider updated",
        "provider_id": provider_id
    }
