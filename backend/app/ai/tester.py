"""Live connectivity test for a configured AI model.

Makes a tiny real request to the provider with the stored credential so an admin
can confirm a key/token actually works (and the model id is valid) before wiring
it into a task. Returns a small, secret-free result: ok / latency / message.

Dispatches by provider family:
  • anthropic        — POST /v1/messages   (x-api-key, or Bearer for OAuth tokens)
  • gemini           — POST /v1beta/models/{model}:generateContent?key=…
  • openai-compatible — POST /chat/completions (Bearer) — OpenAI, DeepSeek,
                        OpenRouter, Perplexity, and unknown/custom providers.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.manager import ai_manager
from app.models.ai_config import AIModel, AIProvider

_TIMEOUT = 20.0
_PING = "ping"


def _family(provider_key: str, base_url: str) -> str:
    """Best-effort provider family for a known key or a custom base URL."""
    if provider_key in ("anthropic", "claude_subscription"):
        return "anthropic"
    if provider_key == "gemini":
        return "gemini"
    if provider_key in ("openai", "deepseek", "openrouter", "perplexity"):
        return "openai"
    # Custom/unknown providers: guess from the base URL.
    u = (base_url or "").lower()
    if "anthropic" in u:
        return "anthropic"
    if "generativelanguage" in u or "gemini" in u:
        return "gemini"
    return "openai"


def _short_error(resp: httpx.Response) -> str:
    """A compact, secret-free reason from a non-2xx provider response."""
    try:
        data = resp.json()
        msg = (
            (data.get("error") or {}).get("message")
            if isinstance(data.get("error"), dict)
            else data.get("error")
        ) or data.get("message")
        if msg:
            return str(msg)[:200]
    except Exception:
        pass
    return (resp.text or "")[:200]


async def test_model(db: AsyncSession, model_id: int) -> Dict[str, Any]:
    """Run a minimal live request for ``model_id``. Never raises."""
    model: Optional[AIModel] = await db.get(AIModel, model_id)
    if model is None:
        return {"ok": False, "message": "Model not found"}
    provider: Optional[AIProvider] = await db.get(AIProvider, model.provider_key)
    if provider is None:
        return {"ok": False, "message": f"Unknown provider: {model.provider_key}"}

    key = ai_manager.effective_api_key(provider)
    if not key:
        noun = "token" if provider.auth_scheme == "oauth_bearer" else "API key"
        return {"ok": False, "message": f"No {noun} configured for {provider.display_name}"}

    from app.ai import catalog
    base_url = (provider.base_url
                or catalog.PROVIDER_CATALOG.get(provider.key, {}).get("base_url")
                or "").rstrip("/")
    if not base_url:
        return {"ok": False, "message": "No base URL for this provider"}

    api_id = model.api_id
    family = _family(provider.key, base_url)
    oauth = provider.auth_scheme == "oauth_bearer"

    if family == "anthropic":
        url = f"{base_url}/v1/messages"
        headers = {"anthropic-version": "2023-06-01", "content-type": "application/json"}
        if oauth:
            headers["authorization"] = f"Bearer {key}"
            headers["anthropic-beta"] = "oauth-2025-04-20"
        else:
            headers["x-api-key"] = key
        payload = {"model": api_id, "max_tokens": 16,
                   "messages": [{"role": "user", "content": _PING}]}
    elif family == "gemini":
        url = f"{base_url}/v1beta/models/{api_id}:generateContent?key={key}"
        headers = {"content-type": "application/json"}
        payload = {"contents": [{"parts": [{"text": _PING}]}],
                   "generationConfig": {"maxOutputTokens": 16}}
    else:  # openai-compatible
        url = f"{base_url}/chat/completions"
        headers = {"authorization": f"Bearer {key}", "content-type": "application/json"}
        payload = {"model": api_id, "max_tokens": 16,
                   "messages": [{"role": "user", "content": _PING}]}

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
        latency_ms = int((time.monotonic() - started) * 1000)
    except httpx.TimeoutException:
        return {"ok": False, "message": f"Timed out after {int(_TIMEOUT)}s"}
    except Exception as exc:  # network/DNS/TLS
        return {"ok": False, "message": f"Connection failed: {type(exc).__name__}"}

    if 200 <= resp.status_code < 300:
        return {"ok": True, "latency_ms": latency_ms,
                "message": f"OK · {latency_ms} ms", "status_code": resp.status_code}
    return {
        "ok": False,
        "latency_ms": latency_ms,
        "status_code": resp.status_code,
        "message": f"{resp.status_code}: {_short_error(resp)}",
    }
