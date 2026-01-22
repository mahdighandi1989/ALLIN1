"""
AI Service
سرویس یکپارچه هوش مصنوعی - پشتیبانی از OpenAI, Anthropic, Google
"""
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class AIService:
    """Unified AI Service supporting multiple providers"""

    def __init__(self):
        self.providers: Dict[str, Dict[str, Any]] = {}
        self._load_providers()

    def _load_providers(self):
        """Load configured providers"""
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = {
                "api_key": settings.OPENAI_API_KEY,
                "model": "gpt-4-turbo-preview",
                "endpoint": "https://api.openai.com/v1/chat/completions"
            }

        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = {
                "api_key": settings.ANTHROPIC_API_KEY,
                "model": "claude-3-sonnet-20240229",
                "endpoint": "https://api.anthropic.com/v1/messages"
            }

        if settings.GOOGLE_AI_API_KEY:
            self.providers["google"] = {
                "api_key": settings.GOOGLE_AI_API_KEY,
                "model": "gemini-pro",
                "endpoint": "https://generativelanguage.googleapis.com/v1beta/models"
            }

    def add_provider(self, provider_id: str, api_key: str, model: str = None):
        """Add or update a provider configuration"""
        if provider_id == "openai":
            self.providers["openai"] = {
                "api_key": api_key,
                "model": model or "gpt-4-turbo-preview",
                "endpoint": "https://api.openai.com/v1/chat/completions"
            }
        elif provider_id == "anthropic":
            self.providers["anthropic"] = {
                "api_key": api_key,
                "model": model or "claude-3-sonnet-20240229",
                "endpoint": "https://api.anthropic.com/v1/messages"
            }
        elif provider_id == "google":
            self.providers["google"] = {
                "api_key": api_key,
                "model": model or "gemini-pro",
                "endpoint": "https://generativelanguage.googleapis.com/v1beta/models"
            }

    def get_available_providers(self) -> List[str]:
        """Get list of configured providers"""
        return list(self.providers.keys())

    def get_default_provider(self) -> Optional[str]:
        """Get default provider"""
        if settings.DEFAULT_AI_PROVIDER in self.providers:
            return settings.DEFAULT_AI_PROVIDER
        if self.providers:
            return list(self.providers.keys())[0]
        return None

    async def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """Generate text using specified or default provider"""
        provider = provider or self.get_default_provider()

        if not provider or provider not in self.providers:
            raise ValueError(f"No AI provider available. Configure at least one provider.")

        config = self.providers[provider]

        try:
            if provider == "openai":
                return await self._call_openai(prompt, system_prompt, config, max_tokens, temperature)
            elif provider == "anthropic":
                return await self._call_anthropic(prompt, system_prompt, config, max_tokens, temperature)
            elif provider == "google":
                return await self._call_google(prompt, system_prompt, config, max_tokens, temperature)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise

    async def _call_openai(self, prompt: str, system_prompt: str, config: dict, max_tokens: int, temperature: float) -> str:
        """Call OpenAI API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                config["endpoint"],
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config["model"],
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str, system_prompt: str, config: dict, max_tokens: int, temperature: float) -> str:
        """Call Anthropic API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            body = {
                "model": config["model"],
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                body["system"] = system_prompt

            response = await client.post(
                config["endpoint"],
                headers={
                    "x-api-key": config["api_key"],
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=body
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def _call_google(self, prompt: str, system_prompt: str, config: dict, max_tokens: int, temperature: float) -> str:
        """Call Google AI API"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        async with httpx.AsyncClient(timeout=120.0) as client:
            url = f"{config['endpoint']}/{config['model']}:generateContent?key={config['api_key']}"
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def analyze_document(self, content: str, analysis_type: str = "summary", provider: str = None) -> str:
        """Analyze document content"""
        prompts = {
            "summary": "Summarize the following document concisely:",
            "risk_assessment": "Analyze the following for potential risks and concerns:",
            "data_extraction": "Extract key data points and entities from the following:"
        }

        system_prompt = "You are a professional document analyst for a banking operations system."
        prompt = f"{prompts.get(analysis_type, prompts['summary'])}\n\n{content}"

        return await self.generate(prompt, provider, system_prompt)

    async def extract_data(self, content: str, provider: str = None) -> Dict[str, Any]:
        """Extract structured data from content"""
        system_prompt = """You are a data extraction AI. Extract structured data and return as JSON.
Categories: customer, facility, property, guarantor, checklist, note
Return format: [{"category": "...", "confidence": 0.0-1.0, "data": {...}}]"""

        result = await self.generate(content, provider, system_prompt, temperature=0.3)

        try:
            # Find JSON in response
            start = result.find('[')
            end = result.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except json.JSONDecodeError:
            pass

        return []


# Global instance
ai_service = AIService()
