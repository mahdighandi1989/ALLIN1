"""
AI Service Module
ماژول یکپارچه‌سازی هوش مصنوعی - پشتیبانی از چندین مدل
"""
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import json
import asyncio
from enum import Enum

from app.core.config import settings


class AIProvider(str, Enum):
    """ارائه‌دهندگان هوش مصنوعی"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


# Database provider cache
_db_providers_cache: Dict[str, Dict[str, Any]] = {}
_db_providers_loaded: bool = False


async def get_db_providers() -> Dict[str, Dict[str, Any]]:
    """Get providers configured in database"""
    global _db_providers_cache, _db_providers_loaded

    if _db_providers_loaded:
        return _db_providers_cache

    try:
        from app.core.database import async_session_maker
        from app.models.settings import SystemSetting
        from sqlalchemy import select

        async with async_session_maker() as session:
            result = await session.execute(
                select(SystemSetting).where(
                    SystemSetting.key.like("ai_provider_%"),
                    SystemSetting.is_active == True
                )
            )
            settings_list = result.scalars().all()

            for setting in settings_list:
                provider_id = setting.key.replace("ai_provider_", "")
                try:
                    data = json.loads(setting.value) if setting.value else {}
                    # If API key exists, consider enabled unless explicitly disabled
                    if data.get("api_key") and data.get("enabled", True) != False:
                        _db_providers_cache[provider_id] = data
                except json.JSONDecodeError:
                    pass

            _db_providers_loaded = True
    except Exception as e:
        print(f"Error loading DB providers: {e}")

    return _db_providers_cache


def refresh_db_providers():
    """Force refresh of database providers cache"""
    global _db_providers_cache, _db_providers_loaded
    _db_providers_cache = {}
    _db_providers_loaded = False


class AIModel(str, Enum):
    """مدل‌های موجود"""
    # OpenAI
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"

    # Anthropic
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_35_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"

    # Google
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"


class BaseAIProvider(ABC):
    """کلاس پایه برای ارائه‌دهندگان AI"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """تولید متن"""
        pass

    @abstractmethod
    async def analyze_document(self, content: str, analysis_type: str) -> Dict[str, Any]:
        """تحلیل سند"""
        pass


class OpenAIProvider(BaseAIProvider):
    """ارائه‌دهنده OpenAI"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = base_url
        self.client = None

    async def _get_client(self):
        if self.client is None:
            from openai import AsyncOpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self.client = AsyncOpenAI(**kwargs)
        return self.client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        return response.choices[0].message.content

    async def analyze_document(self, content: str, analysis_type: str) -> Dict[str, Any]:
        prompts = {
            "risk_assessment": """
                Analyze the following customer/facility information and provide a risk assessment.
                Return a JSON object with:
                - risk_level: "low", "medium", "high"
                - risk_score: 1-100
                - risk_factors: list of identified risk factors
                - recommendations: list of recommendations
            """,
            "data_extraction": """
                Extract structured data from the following document.
                Return a JSON object with all identified fields and their values.
            """,
            "summary": """
                Summarize the following information in a concise manner.
                Return a JSON object with:
                - summary: brief summary
                - key_points: list of key points
                - action_items: list of action items if any
            """,
        }

        system_prompt = prompts.get(analysis_type, prompts["summary"])
        result = await self.generate(
            prompt=f"Document content:\n\n{content}",
            system_prompt=system_prompt,
            temperature=0.3
        )

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_response": result}


class AnthropicProvider(BaseAIProvider):
    """ارائه‌دهنده Anthropic (Claude)"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.base_url = base_url
        self.client = None

    async def _get_client(self):
        if self.client is None:
            from anthropic import AsyncAnthropic
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self.client = AsyncAnthropic(**kwargs)
        return self.client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        client = await self._get_client()

        response = await client.messages.create(
            model=model or self.model,
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful banking operations assistant.",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        return response.content[0].text

    async def analyze_document(self, content: str, analysis_type: str) -> Dict[str, Any]:
        prompts = {
            "risk_assessment": """
                Analyze the following customer/facility information and provide a risk assessment.
                Return a JSON object with:
                - risk_level: "low", "medium", "high"
                - risk_score: 1-100
                - risk_factors: list of identified risk factors
                - recommendations: list of recommendations
            """,
            "data_extraction": """
                Extract structured data from the following document.
                Return a JSON object with all identified fields and their values.
            """,
            "summary": """
                Summarize the following information in a concise manner.
                Return a JSON object with:
                - summary: brief summary
                - key_points: list of key points
                - action_items: list of action items if any
            """,
        }

        system_prompt = prompts.get(analysis_type, prompts["summary"])
        result = await self.generate(
            prompt=f"Document content:\n\n{content}",
            system_prompt=system_prompt,
            temperature=0.3
        )

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_response": result}


class GoogleAIProvider(BaseAIProvider):
    """ارائه‌دهنده Google (Gemini)"""

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or settings.GOOGLE_AI_API_KEY
        self.model = model or settings.GOOGLE_AI_MODEL
        self.base_url = base_url
        self.client = None

    async def _get_client(self):
        if self.client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        return self.client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        client = await self._get_client()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = await asyncio.to_thread(
            client.generate_content,
            full_prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }
        )

        return response.text

    async def analyze_document(self, content: str, analysis_type: str) -> Dict[str, Any]:
        prompts = {
            "risk_assessment": "Analyze and provide risk assessment as JSON with risk_level, risk_score, risk_factors, recommendations.",
            "data_extraction": "Extract structured data as JSON.",
            "summary": "Summarize as JSON with summary, key_points, action_items.",
        }

        system_prompt = prompts.get(analysis_type, prompts["summary"])
        result = await self.generate(
            prompt=f"{system_prompt}\n\nDocument:\n{content}",
            temperature=0.3
        )

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_response": result}


class AIService:
    """
    سرویس یکپارچه هوش مصنوعی
    مدیریت چندین ارائه‌دهنده AI با امکان تغییر داینامیک
    """

    def __init__(self):
        self.providers: Dict[str, BaseAIProvider] = {}
        self._db_providers_initialized = False
        self._initialize_env_providers()

    def _initialize_env_providers(self):
        """راه‌اندازی ارائه‌دهندگان از متغیرهای محیطی"""
        if settings.OPENAI_API_KEY:
            self.providers[AIProvider.OPENAI] = OpenAIProvider()

        if settings.ANTHROPIC_API_KEY:
            self.providers[AIProvider.ANTHROPIC] = AnthropicProvider()

        if settings.GOOGLE_AI_API_KEY:
            self.providers[AIProvider.GOOGLE] = GoogleAIProvider()

    async def _ensure_db_providers(self):
        """Load providers from database if not already loaded"""
        if self._db_providers_initialized:
            return

        try:
            db_providers = await get_db_providers()
            for provider_id, data in db_providers.items():
                api_key = data.get("api_key")
                model = data.get("default_model")
                base_url = data.get("base_url")

                if not api_key:
                    continue

                # Create appropriate provider based on type
                provider_type = data.get("provider_type", "openai_compatible")

                if provider_id == "openai" or provider_type == "openai":
                    self.providers[provider_id] = OpenAIProvider(api_key=api_key, model=model, base_url=base_url)
                elif provider_id == "anthropic" or provider_type == "anthropic":
                    self.providers[provider_id] = AnthropicProvider(api_key=api_key, model=model, base_url=base_url)
                elif provider_id == "google" or provider_type == "google":
                    self.providers[provider_id] = GoogleAIProvider(api_key=api_key, model=model, base_url=base_url)
                elif provider_type == "openai_compatible":
                    # Use OpenAI-compatible provider for others (groq, together, mistral, deepseek, etc.)
                    self.providers[provider_id] = OpenAIProvider(api_key=api_key, model=model, base_url=base_url)

            self._db_providers_initialized = True
        except Exception as e:
            print(f"Error loading database providers: {e}")

    def refresh_providers(self):
        """Refresh providers from database"""
        self._db_providers_initialized = False
        refresh_db_providers()
        # Re-initialize from env
        self.providers = {}
        self._initialize_env_providers()

    async def get_provider(self, provider: Optional[str] = None) -> BaseAIProvider:
        """دریافت ارائه‌دهنده"""
        await self._ensure_db_providers()

        provider = provider or settings.DEFAULT_AI_PROVIDER

        if provider not in self.providers:
            available = list(self.providers.keys())
            if not available:
                raise ValueError("No AI provider configured. Please add API keys in Settings > AI Providers.")
            provider = available[0]

        return self.providers[provider]

    async def get_available_providers(self) -> List[str]:
        """دریافت لیست ارائه‌دهندگان موجود"""
        await self._ensure_db_providers()
        return list(self.providers.keys())

    async def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """تولید متن با AI"""
        ai_provider = await self.get_provider(provider)
        return await ai_provider.generate(prompt, **kwargs)

    async def analyze_document(
        self,
        content: str,
        analysis_type: str = "summary",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """تحلیل سند"""
        ai_provider = await self.get_provider(provider)
        return await ai_provider.analyze_document(content, analysis_type)

    async def extract_customer_data(
        self,
        document_content: str,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """استخراج اطلاعات مشتری از سند"""
        system_prompt = """
        Extract customer information from the document.
        Return a JSON object with these fields (if found):
        - customer_name, account_no, account_type
        - trade_license_no, trade_license_expiry
        - passport_no, passport_expiry
        - emirates_id, emirates_id_expiry
        - phone, email, address
        - Any other relevant information
        """

        ai_provider = await self.get_provider(provider)
        result = await ai_provider.generate(
            prompt=document_content,
            system_prompt=system_prompt,
            temperature=0.2
        )

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_response": result}

    async def generate_summary_report(
        self,
        customer_data: Dict[str, Any],
        facilities_data: List[Dict[str, Any]],
        provider: Optional[str] = None
    ) -> str:
        """تولید گزارش خلاصه"""
        system_prompt = """
        Generate a professional credit file summary report in English.
        Include:
        1. Customer overview
        2. Facilities summary with amounts and types
        3. Security/collateral summary
        4. Risk assessment overview
        5. Key observations and recommendations
        """

        prompt = f"""
        Customer Data: {json.dumps(customer_data, indent=2)}

        Facilities: {json.dumps(facilities_data, indent=2)}
        """

        ai_provider = await self.get_provider(provider)
        return await ai_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )

    async def suggest_missing_fields(
        self,
        profile_data: Dict[str, Any],
        provider: Optional[str] = None
    ) -> List[str]:
        """پیشنهاد فیلدهای ناقص"""
        system_prompt = """
        Analyze the customer profile and identify missing or incomplete fields.
        Return a JSON array of field names that should be completed.
        Focus on critical fields for banking operations and compliance.
        """

        ai_provider = await self.get_provider(provider)
        result = await ai_provider.generate(
            prompt=f"Profile data: {json.dumps(profile_data)}",
            system_prompt=system_prompt,
            temperature=0.2
        )

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return []

    async def assess_risk(
        self,
        customer_data: Dict[str, Any],
        facilities_data: List[Dict[str, Any]] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """ارزیابی ریسک"""
        system_prompt = """
        Perform a risk assessment for this banking customer.
        Return a JSON object with:
        - overall_risk: "low", "medium", "high"
        - risk_score: 1-100
        - categories: {
            "credit_risk": {"level": "", "factors": []},
            "compliance_risk": {"level": "", "factors": []},
            "operational_risk": {"level": "", "factors": []}
          }
        - recommendations: []
        - alerts: []
        """

        data = {
            "customer": customer_data,
            "facilities": facilities_data or []
        }

        ai_provider = await self.get_provider(provider)
        result = await ai_provider.generate(
            prompt=f"Assess risk for: {json.dumps(data)}",
            system_prompt=system_prompt,
            temperature=0.3
        )

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"overall_risk": "unknown", "raw_response": result}


# Singleton instance
ai_service = AIService()
