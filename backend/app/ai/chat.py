"""Multi-turn chat completion for the KB chat — history, native files, web search.

``inference.complete`` is single-shot and ``send_multimodal`` is single-shot with
files; the KB chat needs both PLUS conversation history PLUS an optional live web
search, across the three provider families the app already speaks:

  * anthropic         — /v1/messages (+ the ``web_search`` server tool; PDFs/images
                        as document/image blocks)
  * gemini            — :generateContent (+ ``google_search`` grounding; any file as
                        inlineData)
  * openai-compatible — /chat/completions (images only; Perplexity «sonar» models
                        search the web natively and return ``citations``)

Never raises — returns ``{ok, text, sources, error, model}``. ONE retry on a
transient failure (timeout / 429 / 5xx), per
experiences/ai-call-deadlines-match-the-workload-and-retry-once.md.
"""
from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.ai import catalog
from app.ai.inference import _extract_text, _body_text, _has_temperature, _strip_temperature
from app.ai.tester import _family, _short_error

logger = logging.getLogger(__name__)

TIMEOUT = 180.0
WEB_TIMEOUT = 240.0
_TRANSIENT = {408, 425, 429, 500, 502, 503, 504, 529}


def supports_web(provider_key: str, base_url: str, capabilities: Optional[list] = None,
                 model_id: str = "") -> bool:
    """Can this model search the web in ONE call? Derived from the provider
    family, never from a hand-kept list of model names (the list would rot)."""
    fam = _family(provider_key, base_url or catalog.PROVIDER_CATALOG.get(provider_key, {}).get("base_url", ""))
    if fam in ("anthropic", "gemini"):
        return True
    if provider_key == "perplexity" or "sonar" in (model_id or "").lower():
        return True
    return "web_search" in set(capabilities or [])


def _b64(d: bytes) -> str:
    return base64.b64encode(d).decode("ascii")


def _sources_anthropic(data: Dict[str, Any]) -> List[Dict[str, str]]:
    out: Dict[str, str] = {}
    for b in data.get("content") or []:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "web_search_tool_result":
            for r in (b.get("content") or []):
                if isinstance(r, dict) and r.get("url"):
                    out.setdefault(r["url"], r.get("title") or r["url"])
        for c in b.get("citations") or []:
            if isinstance(c, dict) and c.get("url"):
                out[c["url"]] = c.get("title") or out.get(c["url"]) or c["url"]
    return [{"url": u, "title": t} for u, t in out.items()]


def _sources_gemini(data: Dict[str, Any]) -> List[Dict[str, str]]:
    out: Dict[str, str] = {}
    for cand in data.get("candidates") or []:
        gm = cand.get("groundingMetadata") or {}
        for ch in gm.get("groundingChunks") or []:
            w = ch.get("web") or {}
            if w.get("uri"):
                out.setdefault(w["uri"], w.get("title") or w["uri"])
    return [{"url": u, "title": t} for u, t in out.items()]


def _sources_openai(data: Dict[str, Any]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for c in data.get("citations") or []:           # Perplexity
        if isinstance(c, str):
            out.append({"url": c, "title": c})
        elif isinstance(c, dict) and c.get("url"):
            out.append({"url": c["url"], "title": c.get("title") or c["url"]})
    for r in data.get("search_results") or []:
        if isinstance(r, dict) and r.get("url") and not any(o["url"] == r["url"] for o in out):
            out.append({"url": r["url"], "title": r.get("title") or r["url"]})
    return out


def build_request(resolved, *, system: str, turns: List[Dict[str, str]],
                  files: List[Dict[str, Any]], web: bool, max_tokens: int):
    """Return (family, url, headers, payload) for one chat request.

    ``turns`` = prior [{role: user|assistant, content}] ending with the CURRENT
    user turn; ``files`` ([{filename, mimetype, data}]) ride on that last turn.
    """
    base_url = (resolved.base_url or catalog.PROVIDER_CATALOG.get(resolved.provider_key, {}).get("base_url") or "").rstrip("/")
    family = _family(resolved.provider_key, base_url)
    oauth = resolved.auth_scheme == "oauth_bearer"
    key = resolved.api_key
    api_id = resolved.model_key
    last = len(turns) - 1

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
        msgs: List[Dict[str, Any]] = []
        for i, t in enumerate(turns):
            if i == last and files:
                content: list = []
                for f in files:
                    mt = (f.get("mimetype") or "").lower()
                    if mt == "application/pdf":
                        content.append({"type": "document", "source": {"type": "base64", "media_type": mt, "data": _b64(f["data"])}})
                    elif mt.startswith("image/"):
                        content.append({"type": "image", "source": {"type": "base64", "media_type": mt, "data": _b64(f["data"])}})
                content.append({"type": "text", "text": t["content"]})
                msgs.append({"role": t["role"], "content": content})
            else:
                msgs.append({"role": t["role"], "content": t["content"]})
        payload: Dict[str, Any] = {"model": api_id, "max_tokens": max_tokens, "messages": msgs}
        blocks = []
        if oauth:
            blocks.append({"type": "text", "text": catalog.CLAUDE_CODE_SYSTEM})
        blocks.append({"type": "text", "text": system})
        payload["system"] = blocks if oauth else system
        if web:
            payload["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
    elif family == "gemini":
        gid = "-".join((api_id or "").strip().removeprefix("models/").split()).lower()
        url = f"{base_url}/v1beta/models/{gid}:generateContent?key={key}"
        headers = {"content-type": "application/json"}
        contents = []
        for i, t in enumerate(turns):
            parts: list = []
            if i == last:
                for f in files:
                    parts.append({"inlineData": {"mimeType": f.get("mimetype") or "application/octet-stream", "data": _b64(f["data"])}})
            parts.append({"text": t["content"]})
            contents.append({"role": "model" if t["role"] == "assistant" else "user", "parts": parts})
        payload = {"contents": contents, "systemInstruction": {"parts": [{"text": system}]},
                   "generationConfig": {"maxOutputTokens": max_tokens}}
        if web:
            payload["tools"] = [{"google_search": {}}]
    else:  # openai-compatible
        url = f"{base_url}/chat/completions"
        headers = {"authorization": f"Bearer {key}", "content-type": "application/json"}
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        for i, t in enumerate(turns):
            if i == last and files:
                parts = []
                for f in files:
                    mt = (f.get("mimetype") or "").lower()
                    if mt.startswith("image/"):
                        parts.append({"type": "image_url", "image_url": {"url": f"data:{mt};base64,{_b64(f['data'])}"}})
                parts.append({"type": "text", "text": t["content"]})
                messages.append({"role": t["role"], "content": parts})
            else:
                messages.append({"role": t["role"], "content": t["content"]})
        payload = {"model": api_id, "max_tokens": max_tokens, "messages": messages}
    return family, url, headers, payload


async def chat(resolved, *, system: str, turns: List[Dict[str, str]],
               files: Optional[List[Dict[str, Any]]] = None, web: bool = False,
               max_tokens: int = 8000) -> Dict[str, Any]:
    files = files or []
    name = resolved.display_name
    family, url, headers, payload = build_request(
        resolved, system=system, turns=turns, files=files, web=web, max_tokens=max_tokens)
    deadline = WEB_TIMEOUT if web else TIMEOUT

    resp = None
    err = ""
    for attempt in (1, 2):
        try:
            async with httpx.AsyncClient(timeout=deadline) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 400 and "temperature" in _body_text(resp).lower() and _has_temperature(payload):
                    _strip_temperature(payload)
                    resp = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException:
            resp, err = None, f"timed out after {int(deadline)}s"
        except Exception as exc:  # network/DNS/TLS
            resp, err = None, f"connection failed: {type(exc).__name__}"
        transient = resp is None or resp.status_code in _TRANSIENT
        if not transient or attempt == 2:
            break
        await asyncio.sleep(2.0)

    if resp is None:
        return {"ok": False, "error": err, "text": "", "sources": [], "model": name}
    if not (200 <= resp.status_code < 300):
        return {"ok": False, "error": f"{resp.status_code}: {_short_error(resp)}", "text": "", "sources": [], "model": name}
    try:
        data = resp.json()
    except Exception:
        return {"ok": False, "error": "invalid provider response", "text": "", "sources": [], "model": name}
    text = _extract_text(family, data)
    if not text:
        return {"ok": False, "error": "empty response", "text": "", "sources": [], "model": name}
    if family == "anthropic":
        sources = _sources_anthropic(data)
    elif family == "gemini":
        sources = _sources_gemini(data)
    else:
        sources = _sources_openai(data)
    return {"ok": True, "text": text, "sources": sources, "error": None, "model": name}
