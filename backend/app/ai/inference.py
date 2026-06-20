"""Text completion against the panel's configured AI model.

This is the runtime counterpart to :mod:`app.ai.tester` (which only pings a
model). It resolves an application task to a usable model via
:data:`app.ai.ai_manager`, calls the provider with the stored credential, and
returns the model's text answer. Used by the Telegram AI bridge and available to
any other feature that needs a one-shot completion.

Dispatches by provider family, mirroring the catalog/tester wiring:
  • anthropic        — POST /v1/messages   (x-api-key, or Bearer for OAuth tokens)
  • gemini           — POST /v1beta/models/{model}:generateContent?key=…
  • openai-compatible — POST /chat/completions (Bearer) — OpenAI, DeepSeek, …

Never raises — returns ``{ok, text, model, error}``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import ai_manager
from app.ai.tester import _family, _short_error

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


def _extract_text(family: str, data: Dict[str, Any]) -> str:
    """Pull the assistant's text out of a provider response body."""
    try:
        if family == "anthropic":
            blocks = data.get("content") or []
            return "".join(
                b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"
            ).strip()
        if family == "gemini":
            cands = data.get("candidates") or []
            if not cands:
                return ""
            parts = (cands[0].get("content") or {}).get("parts") or []
            return "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
        # openai-compatible
        choices = data.get("choices") or []
        if not choices:
            return ""
        return ((choices[0].get("message") or {}).get("content") or "").strip()
    except Exception:  # pragma: no cover - defensive parsing
        return ""


async def complete(
    db: AsyncSession,
    prompt: str,
    *,
    task: str = "chat",
    system: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
    model_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Resolve ``task`` (or an explicit ``model_id``) to a model and complete ``prompt``.

    Falls back to the ``general`` task when ``task`` has no usable model. Returns
    ``{"ok": False, "error": "no_model"}`` when nothing is configured.
    """
    resolved = None
    if model_id is not None:
        resolved = await ai_manager.resolve_specific(db, model_id, task)
    if resolved is None or not resolved.is_usable:
        resolved = await ai_manager.resolve(db, task)
    if resolved is None or not resolved.is_usable:
        resolved = await ai_manager.resolve(db, "general")
    if resolved is None or not resolved.is_usable:
        return {"ok": False, "error": "no_model", "text": "", "model": None}

    from app.ai import catalog

    base_url = (
        resolved.base_url
        or catalog.PROVIDER_CATALOG.get(resolved.provider_key, {}).get("base_url")
        or ""
    ).rstrip("/")
    if not base_url:
        return {"ok": False, "error": "no_base_url", "text": "", "model": resolved.display_name}

    family = _family(resolved.provider_key, base_url)
    oauth = resolved.auth_scheme == "oauth_bearer"
    key = resolved.api_key
    api_id = resolved.model_key
    temp = resolved.temperature if temperature is None else temperature

    if family == "anthropic":
        url = f"{base_url}/v1/messages"
        headers = {"anthropic-version": "2023-06-01", "content-type": "application/json"}
        if oauth:
            headers["authorization"] = f"Bearer {key}"
            headers["anthropic-beta"] = "oauth-2025-04-20"
            headers["user-agent"] = "claude-cli/1.0 (external)"
        else:
            headers["x-api-key"] = key
        payload: Dict[str, Any] = {
            "model": api_id,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if oauth:
            # Subscription tokens require Claude Code's system prefix first; keep
            # the app's own system prompt as a second block.
            blocks = [{"type": "text", "text": catalog.CLAUDE_CODE_SYSTEM}]
            if system:
                blocks.append({"type": "text", "text": system})
            payload["system"] = blocks
        elif system:
            payload["system"] = system
        if temp is not None:
            payload["temperature"] = temp
    elif family == "gemini":
        # Google model ids are lowercase-hyphenated; tolerate "models/" prefix,
        # stray spaces and casing (e.g. "Gemini 2.5 Flash" → "gemini-2.5-flash").
        gid = "-".join((api_id or "").strip().removeprefix("models/").split()).lower()
        url = f"{base_url}/v1beta/models/{gid}:generateContent?key={key}"
        headers = {"content-type": "application/json"}
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if temp is not None:
            payload["generationConfig"]["temperature"] = temp
    else:  # openai-compatible
        url = f"{base_url}/chat/completions"
        headers = {"authorization": f"Bearer {key}", "content-type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": api_id, "max_tokens": max_tokens, "messages": messages}
        if temp is not None:
            payload["temperature"] = temp

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        return {"ok": False, "error": f"timed out after {int(_TIMEOUT)}s", "text": "", "model": resolved.display_name}
    except Exception as exc:  # network/DNS/TLS
        return {"ok": False, "error": f"connection failed: {type(exc).__name__}", "text": "", "model": resolved.display_name}

    if not (200 <= resp.status_code < 300):
        return {
            "ok": False,
            "error": f"{resp.status_code}: {_short_error(resp)}",
            "text": "",
            "model": resolved.display_name,
        }

    try:
        data = resp.json()
    except Exception:
        return {"ok": False, "error": "invalid provider response", "text": "", "model": resolved.display_name}

    text = _extract_text(family, data)
    if not text:
        return {"ok": False, "error": "empty response", "text": "", "model": resolved.display_name}
    return {"ok": True, "text": text, "model": resolved.display_name, "error": None}


# ---------------------------------------------------------------------------
# Multimodal completion — send a document/image (PDF, PNG, JPG, …) to a
# vision/document-capable model and get text back. Used by the AI document
# import/extraction pipeline.
# ---------------------------------------------------------------------------
async def complete_multimodal(
    db: AsyncSession,
    prompt: str,
    files: list,                      # [{filename, mimetype, data: bytes}]
    *,
    model_id: Optional[int] = None,
    task: str = "document_extraction",
    system: Optional[str] = None,
    max_tokens: int = 8000,
) -> Dict[str, Any]:
    """Run an extraction over ``files`` with a chosen (or auto) model.

    Returns ``{ok, text, model}`` on success, or ``{ok: False, error, suggestions}``
    where ``error`` is "no_model" / "model_incapable" / "<provider error>".
    """
    import base64
    from app.ai import catalog

    resolved = None
    if model_id is not None:
        resolved = await ai_manager.resolve_specific(db, model_id, task)
    if resolved is None:
        resolved = await ai_manager.resolve(db, task) or await ai_manager.resolve(db, "general")
    if resolved is None or not resolved.is_usable:
        return {"ok": False, "error": "no_model", "text": "", "model": None}

    needs_pdf = any((f.get("mimetype") or "").lower() == "application/pdf" for f in files)
    caps = set(resolved.capabilities or [])
    # Text-only (no binary files) needs no vision/documents capability.
    cap_ok = True if not files else (("documents" in caps) if needs_pdf else (("vision" in caps) or ("documents" in caps)))
    if not cap_ok:
        suggestions = await ai_manager.capable_models(db, "documents" if needs_pdf else "vision")
        return {"ok": False, "error": "model_incapable", "model": resolved.display_name,
                "suggestions": [s for s in suggestions if s["id"] != getattr(resolved, "model_id_db", None)],
                "text": ""}

    base_url = (resolved.base_url
                or catalog.PROVIDER_CATALOG.get(resolved.provider_key, {}).get("base_url") or "").rstrip("/")
    family = _family(resolved.provider_key, base_url)
    oauth = resolved.auth_scheme == "oauth_bearer"
    key = resolved.api_key
    api_id = resolved.model_key

    def b64(d):
        return base64.b64encode(d).decode("ascii")

    if family == "anthropic":
        url = f"{base_url}/v1/messages"
        betas = ["pdfs-2024-09-25"]
        if oauth:
            betas.append("oauth-2025-04-20")
        headers = {"anthropic-version": "2023-06-01", "content-type": "application/json",
                   "anthropic-beta": ",".join(betas)}
        if oauth:
            headers["authorization"] = f"Bearer {key}"
            headers["user-agent"] = "claude-cli/1.0 (external)"
        else:
            headers["x-api-key"] = key
        content: list = []
        for f in files:
            mt = (f.get("mimetype") or "").lower()
            if mt == "application/pdf":
                content.append({"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64(f["data"])}})
            elif mt.startswith("image/"):
                content.append({"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64(f["data"])}})
        content.append({"type": "text", "text": prompt})
        payload: Dict[str, Any] = {"model": api_id, "max_tokens": max_tokens, "messages": [{"role": "user", "content": content}]}
        sys_blocks = []
        if oauth:
            sys_blocks.append({"type": "text", "text": catalog.CLAUDE_CODE_SYSTEM})
        if system:
            sys_blocks.append({"type": "text", "text": system})
        if sys_blocks:
            payload["system"] = sys_blocks
    elif family == "gemini":
        gid = "-".join((api_id or "").strip().removeprefix("models/").split()).lower()
        url = f"{base_url}/v1beta/models/{gid}:generateContent?key={key}"
        headers = {"content-type": "application/json"}
        parts: list = []
        for f in files:
            parts.append({"inlineData": {"mimeType": f.get("mimetype") or "application/octet-stream", "data": b64(f["data"])}})
        parts.append({"text": prompt})
        payload = {"contents": [{"role": "user", "parts": parts}],
                   "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0}}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
    else:  # openai-compatible — images only (no native PDF)
        url = f"{base_url}/chat/completions"
        headers = {"authorization": f"Bearer {key}", "content-type": "application/json"}
        parts = []
        for f in files:
            mt = (f.get("mimetype") or "").lower()
            if mt.startswith("image/"):
                parts.append({"type": "image_url", "image_url": {"url": f"data:{mt};base64,{b64(f['data'])}"}})
        parts.append({"type": "text", "text": prompt})
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": parts}]
        payload = {"model": api_id, "max_tokens": max_tokens, "messages": messages}

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        return {"ok": False, "error": "timed out (large file?)", "text": "", "model": resolved.display_name}
    except Exception as exc:
        return {"ok": False, "error": f"connection failed: {type(exc).__name__}", "text": "", "model": resolved.display_name}
    if not (200 <= resp.status_code < 300):
        return {"ok": False, "error": f"{resp.status_code}: {_short_error(resp)}", "text": "", "model": resolved.display_name}
    try:
        data = resp.json()
    except Exception:
        return {"ok": False, "error": "invalid provider response", "text": "", "model": resolved.display_name}
    text = _extract_text(family, data)
    if not text:
        return {"ok": False, "error": "empty response", "text": "", "model": resolved.display_name}
    return {"ok": True, "text": text, "model": resolved.display_name, "error": None}
