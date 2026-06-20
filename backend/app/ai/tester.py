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
        payload = {"model": api_id, "max_tokens": 16,
                   "messages": [{"role": "user", "content": _PING}]}
        if oauth:
            headers["authorization"] = f"Bearer {key}"
            headers["anthropic-beta"] = "oauth-2025-04-20"
            headers["user-agent"] = "claude-cli/1.0 (external)"
            # Subscription (OAuth) tokens require Claude Code's system prefix.
            payload["system"] = [{"type": "text", "text": catalog.CLAUDE_CODE_SYSTEM}]
        else:
            headers["x-api-key"] = key
    elif family == "gemini":
        # Google model ids are lowercase-hyphenated; tolerate "models/" prefix,
        # stray spaces and casing (e.g. "Gemini 2.5 Flash" → "gemini-2.5-flash").
        api_id = "-".join((api_id or "").strip().removeprefix("models/").split()).lower()
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

    detail = _short_error(resp)
    if resp.status_code == 429:
        # Rate-limited: the credential is valid (it authenticated). For a
        # subscription/OAuth token this quota is shared with your Claude Code &
        # claude.ai usage and resets over time — so it's not a broken token.
        retry = resp.headers.get("retry-after")
        if oauth:
            msg = ("subscription quota for this model is busy/exhausted "
                   "(shared with your Claude Code & claude.ai usage)")
        else:
            msg = "rate limited (account/plan quota)"
        if retry:
            msg += f" — retry in {retry}s"
        return {"ok": False, "latency_ms": latency_ms, "status_code": 429,
                "message": f"429: {msg}"}
    # Other errors: include the provider's reason when it's meaningful.
    suffix = f": {detail}" if detail and detail.lower() != "error" else ""
    return {
        "ok": False,
        "latency_ms": latency_ms,
        "status_code": resp.status_code,
        "message": f"{resp.status_code}{suffix}",
    }


# ---------------------------------------------------------------------------
# Live model discovery — pull the provider's current model list and reconcile
# it into the DB so new models appear and removed ones disappear, instead of
# relying on the hardcoded catalog. Custom (admin-added) models are preserved.
# ---------------------------------------------------------------------------
def _capabilities_for(family: str, model_id: str) -> list:
    """Heuristic default capabilities for a freshly-discovered model id."""
    from app.ai.catalog import Capability as C
    mid = model_id.lower()
    if family == "anthropic":
        if "haiku" in mid:
            return [C.TEXT.value, C.VISION.value, C.FAST.value, C.STRUCTURED_OUTPUT.value]
        return [C.TEXT.value, C.VISION.value, C.REASONING.value, C.LONG_CONTEXT.value,
                C.CODE.value, C.STRUCTURED_OUTPUT.value, C.DOCUMENTS.value]
    if family == "gemini":
        caps = [C.TEXT.value, C.VISION.value, C.LONG_CONTEXT.value, C.DOCUMENTS.value]
        if "flash" in mid:
            caps.append(C.FAST.value)
        return caps
    # openai-compatible
    caps = [C.TEXT.value, C.CODE.value, C.STRUCTURED_OUTPUT.value]
    if any(x in mid for x in ("4o", "vision", "o1", "o3", "o4")):
        caps.append(C.VISION.value)
    if any(x in mid for x in ("mini", "nano", "flash", "haiku", "small")):
        caps.append(C.FAST.value)
    return caps


async def _fetch_live_models(family: str, base_url: str, key: str, oauth: bool) -> list:
    """Return ``[(model_id, display_name)]`` from the provider's models API."""
    if family == "anthropic":
        url = f"{base_url}/v1/models?limit=1000"
        headers = {"anthropic-version": "2023-06-01"}
        if oauth:
            headers["authorization"] = f"Bearer {key}"
            headers["anthropic-beta"] = "oauth-2025-04-20"
        else:
            headers["x-api-key"] = key
    elif family == "gemini":
        url = f"{base_url}/v1beta/models?key={key}&pageSize=1000"
        headers = {}
    else:
        url = f"{base_url}/models"
        headers = {"authorization": f"Bearer {key}"}

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url, headers=headers)
    if not (200 <= resp.status_code < 300):
        raise RuntimeError(f"{resp.status_code}: {_short_error(resp)}")
    data = resp.json()

    out = []
    if family == "gemini":
        for m in data.get("models", []):
            methods = m.get("supportedGenerationMethods") or []
            if "generateContent" not in methods:
                continue
            mid = str(m.get("name", "")).split("/")[-1]
            if mid:
                out.append((mid, m.get("displayName") or mid))
    else:  # anthropic + openai both use {"data": [...]}
        for m in data.get("data", []):
            mid = m.get("id")
            if mid:
                out.append((mid, m.get("display_name") or mid))
    return out


async def sync_provider_models(db: AsyncSession, provider_key: str) -> Dict[str, Any]:
    """Refresh a provider's models from its live API. Reconciles the DB.

    Adds newly-available models, updates display names, and removes
    catalog/discovered models the provider no longer lists. Admin-added (custom)
    models are never touched. Never raises — returns ``{ok, ...}``.
    """
    from sqlalchemy import select
    from app.ai import catalog

    provider: Optional[AIProvider] = await db.get(AIProvider, provider_key)
    if provider is None:
        return {"ok": False, "message": f"Unknown provider: {provider_key}"}
    key = ai_manager.effective_api_key(provider)
    if not key:
        noun = "token" if provider.auth_scheme == "oauth_bearer" else "API key"
        return {"ok": False, "message": f"No {noun} configured for {provider.display_name}"}

    base_url = (provider.base_url
                or catalog.PROVIDER_CATALOG.get(provider.key, {}).get("base_url")
                or "").rstrip("/")
    family = _family(provider.key, base_url)
    oauth = provider.auth_scheme == "oauth_bearer"

    try:
        live = await _fetch_live_models(family, base_url, key, oauth)
    except Exception as exc:
        return {"ok": False, "message": f"Could not list models: {exc}"}
    if not live:
        return {"ok": False, "message": "Provider returned no models"}

    existing = (
        await db.execute(select(AIModel).where(AIModel.provider_key == provider_key))
    ).scalars().all()
    by_api_id = {m.api_id: m for m in existing}
    live_ids = set()
    added = updated = removed = 0

    for mid, name in live:
        live_ids.add(mid)
        m = by_api_id.get(mid)
        if m is None:
            db.add(AIModel(
                model_key=f"{provider_key}:{mid}",
                api_model_id=mid,
                provider_key=provider_key,
                display_name=name,
                enabled=True,
                capabilities=_capabilities_for(family, mid),
                priority=5,
                source="discovered",
                is_custom=False,
            ))
            added += 1
        elif (m.source or "catalog") != "custom":
            m.display_name = name or m.display_name
            if not m.capabilities:
                m.capabilities = _capabilities_for(family, mid)
            if (m.source or "catalog") == "catalog":
                m.source = "discovered"
            updated += 1

    for m in existing:
        if (m.source or "catalog") != "custom" and m.api_id not in live_ids:
            await db.delete(m)
            removed += 1

    await db.commit()
    return {
        "ok": True,
        "added": added,
        "updated": updated,
        "removed": removed,
        "total": len(live_ids),
        "message": f"Synced {len(live_ids)} models · +{added} new, {removed} removed",
    }
