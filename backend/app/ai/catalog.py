"""The static AI catalog: providers, models, capabilities, and task types.

This is code-defined seed data — the *menu* of what the panel could use. The
live, editable state (enabled flags, API keys, routing) lives in the database
(see :mod:`app.models.ai_config`); on first run the rows here are copied in, and
the self-healing bootstrap keeps catalog models refreshed without clobbering
admin-added ones.

Model ids below are real provider model identifiers. The default/recommended
provider is Anthropic and the default model is ``claude-opus-4-8`` (the most
capable Claude model); other providers ship disabled until a key is added.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, TypedDict


# ---------------------------------------------------------------------------
# Capabilities — what a model can do. Used to auto-pick a model for a task when
# no explicit route is set, and shown as chips in the UI.
# ---------------------------------------------------------------------------
class Capability(str, Enum):
    TEXT = "text"
    VISION = "vision"               # understands images
    REASONING = "reasoning"         # strong multi-step reasoning
    LONG_CONTEXT = "long_context"   # large context window
    FAST = "fast"                   # low latency / cheap
    CODE = "code"
    STRUCTURED_OUTPUT = "structured_output"  # reliable JSON / schema output
    DOCUMENTS = "documents"         # PDF / document understanding
    WEB_SEARCH = "web_search"       # live web access (e.g. Perplexity)


CAPABILITIES = [
    {"id": Capability.TEXT.value, "label": "Text"},
    {"id": Capability.VISION.value, "label": "Vision / Images"},
    {"id": Capability.REASONING.value, "label": "Reasoning"},
    {"id": Capability.LONG_CONTEXT.value, "label": "Long context"},
    {"id": Capability.FAST.value, "label": "Fast / cheap"},
    {"id": Capability.CODE.value, "label": "Code"},
    {"id": Capability.STRUCTURED_OUTPUT.value, "label": "Structured output"},
    {"id": Capability.DOCUMENTS.value, "label": "Documents / PDF"},
    {"id": Capability.WEB_SEARCH.value, "label": "Web search"},
]


# ---------------------------------------------------------------------------
# Application tasks — the places in the panel where an AI model gets used. Each
# task is a routing key: a consumer resolves a task to a model. ``preferred``
# is the capability used to auto-pick a model when no explicit route exists.
# ---------------------------------------------------------------------------
class AITask(str, Enum):
    GENERAL = "general"
    CHAT = "chat"
    DOCUMENT_EXTRACTION = "document_extraction"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    REPORT_DRAFTING = "report_drafting"
    TRANSLATION = "translation"
    DATA_VALIDATION = "data_validation"


TASK_TYPES = [
    {
        "id": AITask.GENERAL.value,
        "label": "General",
        "description": "Default model for any AI feature without a specific route.",
        "preferred": Capability.REASONING.value,
    },
    {
        "id": AITask.CHAT.value,
        "label": "Assistant chat",
        "description": "Conversational Q&A about customers, facilities, and the book.",
        "preferred": Capability.REASONING.value,
    },
    {
        "id": AITask.DOCUMENT_EXTRACTION.value,
        "label": "Document extraction",
        "description": "Read uploaded documents/images (KYC, statements) and pull out fields.",
        "preferred": Capability.VISION.value,
    },
    {
        "id": AITask.SUMMARIZATION.value,
        "label": "Summarization",
        "description": "Summarize customer files, facility notes, and long threads.",
        "preferred": Capability.LONG_CONTEXT.value,
    },
    {
        "id": AITask.CLASSIFICATION.value,
        "label": "Classification",
        "description": "Tag, route, and categorize records and free text.",
        "preferred": Capability.FAST.value,
    },
    {
        "id": AITask.REPORT_DRAFTING.value,
        "label": "Report drafting",
        "description": "Draft reports, offer letters, and credit notes.",
        "preferred": Capability.REASONING.value,
    },
    {
        "id": AITask.TRANSLATION.value,
        "label": "Translation",
        "description": "Translate between English, Arabic, and Persian.",
        "preferred": Capability.TEXT.value,
    },
    {
        "id": AITask.DATA_VALIDATION.value,
        "label": "Data validation",
        "description": "Sanity-check imported data and flag inconsistencies.",
        "preferred": Capability.STRUCTURED_OUTPUT.value,
    },
]


# ---------------------------------------------------------------------------
# Provider + model catalog
# ---------------------------------------------------------------------------
class _ModelDef(TypedDict, total=False):
    model_key: str
    api_model_id: str   # actual id sent to the provider (defaults to model_key)
    display_name: str
    capabilities: List[str]
    max_output_tokens: int
    context_window: int
    input_cost_per_1m: float
    output_cost_per_1m: float
    priority: int


class _ProviderDef(TypedDict, total=False):
    display_name: str
    base_url: str
    env_key: str
    auth_scheme: str    # "api_key" (default) or "oauth_bearer"
    recommended: bool
    notes: str
    models: List[_ModelDef]


_TEXT = Capability.TEXT.value
_VISION = Capability.VISION.value
_REASON = Capability.REASONING.value
_LONG = Capability.LONG_CONTEXT.value
_FAST = Capability.FAST.value
_CODE = Capability.CODE.value
_STRUCT = Capability.STRUCTURED_OUTPUT.value
_DOCS = Capability.DOCUMENTS.value
_WEB = Capability.WEB_SEARCH.value


PROVIDER_CATALOG: Dict[str, _ProviderDef] = {
    # Claude via a subscription / Claude Code OAuth token. Uses your existing
    # plan instead of a separately-billed API key — the token (sk-ant-oat01-…)
    # is sent as a Bearer credential. Same Claude models as the API-key provider.
    "claude_subscription": {
        "display_name": "Claude (subscription · OAuth token)",
        "base_url": "https://api.anthropic.com",
        "env_key": "CLAUDE_CODE_OAUTH_TOKEN",
        "auth_scheme": "oauth_bearer",
        "recommended": True,
        "notes": "Recommended if you have a Claude / Claude Code subscription. "
                 "Uses your OAuth token (sk-ant-oat01-…) — no separate API billing.",
        "models": [
            {
                "model_key": "claude-opus-4-8-sub",
                "api_model_id": "claude-opus-4-8",
                "display_name": "Claude Opus 4.8 (subscription)",
                "capabilities": [_TEXT, _VISION, _REASON, _LONG, _CODE, _STRUCT, _DOCS],
                "max_output_tokens": 128000,
                "context_window": 1000000,
                "priority": 1,
            },
            {
                "model_key": "claude-sonnet-4-6-sub",
                "api_model_id": "claude-sonnet-4-6",
                "display_name": "Claude Sonnet 4.6 (subscription)",
                "capabilities": [_TEXT, _VISION, _REASON, _LONG, _CODE, _STRUCT, _DOCS],
                "max_output_tokens": 64000,
                "context_window": 1000000,
                "priority": 2,
            },
            {
                "model_key": "claude-haiku-4-5-sub",
                "api_model_id": "claude-haiku-4-5",
                "display_name": "Claude Haiku 4.5 (subscription)",
                "capabilities": [_TEXT, _VISION, _FAST, _STRUCT],
                "max_output_tokens": 64000,
                "context_window": 200000,
                "priority": 3,
            },
        ],
    },
    "anthropic": {
        "display_name": "Anthropic (Claude · API key)",
        "base_url": "https://api.anthropic.com",
        "env_key": "ANTHROPIC_API_KEY",
        "auth_scheme": "api_key",
        "notes": "Pay-per-use Claude API key — strong reasoning, vision, and long context.",
        "models": [
            {
                "model_key": "claude-opus-4-8",
                "display_name": "Claude Opus 4.8",
                "capabilities": [_TEXT, _VISION, _REASON, _LONG, _CODE, _STRUCT, _DOCS],
                "max_output_tokens": 128000,
                "context_window": 1000000,
                "input_cost_per_1m": 5.0,
                "output_cost_per_1m": 25.0,
                "priority": 1,
            },
            {
                "model_key": "claude-sonnet-4-6",
                "display_name": "Claude Sonnet 4.6",
                "capabilities": [_TEXT, _VISION, _REASON, _LONG, _CODE, _STRUCT, _DOCS],
                "max_output_tokens": 64000,
                "context_window": 1000000,
                "input_cost_per_1m": 3.0,
                "output_cost_per_1m": 15.0,
                "priority": 2,
            },
            {
                "model_key": "claude-haiku-4-5",
                "display_name": "Claude Haiku 4.5",
                "capabilities": [_TEXT, _VISION, _FAST, _STRUCT],
                "max_output_tokens": 64000,
                "context_window": 200000,
                "input_cost_per_1m": 1.0,
                "output_cost_per_1m": 5.0,
                "priority": 3,
            },
        ],
    },
    "openai": {
        "display_name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "notes": "GPT models.",
        "models": [
            {
                "model_key": "gpt-4o",
                "display_name": "GPT-4o",
                "capabilities": [_TEXT, _VISION, _REASON, _CODE, _STRUCT],
                "max_output_tokens": 16384,
                "context_window": 128000,
                "input_cost_per_1m": 2.5,
                "output_cost_per_1m": 10.0,
                "priority": 4,
            },
            {
                "model_key": "gpt-4o-mini",
                "display_name": "GPT-4o mini",
                "capabilities": [_TEXT, _VISION, _FAST, _STRUCT],
                "max_output_tokens": 16384,
                "context_window": 128000,
                "input_cost_per_1m": 0.15,
                "output_cost_per_1m": 0.6,
                "priority": 5,
            },
        ],
    },
    "gemini": {
        "display_name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com",
        "env_key": "GEMINI_API_KEY",
        "notes": "Gemini models — large context and strong vision.",
        "models": [
            {
                "model_key": "gemini-1.5-pro",
                "display_name": "Gemini 1.5 Pro",
                "capabilities": [_TEXT, _VISION, _REASON, _LONG, _DOCS],
                "max_output_tokens": 8192,
                "context_window": 2000000,
                "input_cost_per_1m": 1.25,
                "output_cost_per_1m": 5.0,
                "priority": 5,
            },
            {
                "model_key": "gemini-1.5-flash",
                "display_name": "Gemini 1.5 Flash",
                "capabilities": [_TEXT, _VISION, _FAST, _LONG],
                "max_output_tokens": 8192,
                "context_window": 1000000,
                "input_cost_per_1m": 0.075,
                "output_cost_per_1m": 0.3,
                "priority": 6,
            },
        ],
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
        "notes": "Cost-effective text and reasoning models.",
        "models": [
            {
                "model_key": "deepseek-chat",
                "display_name": "DeepSeek Chat",
                "capabilities": [_TEXT, _CODE, _FAST],
                "max_output_tokens": 8192,
                "context_window": 64000,
                "input_cost_per_1m": 0.27,
                "output_cost_per_1m": 1.1,
                "priority": 6,
            },
            {
                "model_key": "deepseek-reasoner",
                "display_name": "DeepSeek Reasoner",
                "capabilities": [_TEXT, _REASON, _CODE],
                "max_output_tokens": 8192,
                "context_window": 64000,
                "input_cost_per_1m": 0.55,
                "output_cost_per_1m": 2.19,
                "priority": 6,
            },
        ],
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "notes": "Gateway to many models. Add the specific models you want as custom entries.",
        "models": [],
    },
    "perplexity": {
        "display_name": "Perplexity",
        "base_url": "https://api.perplexity.ai",
        "env_key": "PERPLEXITY_API_KEY",
        "notes": "Live web search and research.",
        "models": [
            {
                "model_key": "sonar",
                "display_name": "Sonar",
                "capabilities": [_TEXT, _WEB, _FAST],
                "max_output_tokens": 8192,
                "context_window": 128000,
                "priority": 7,
            },
            {
                "model_key": "sonar-pro",
                "display_name": "Sonar Pro",
                "capabilities": [_TEXT, _WEB, _REASON],
                "max_output_tokens": 8192,
                "context_window": 200000,
                "priority": 7,
            },
        ],
    },
}


# The provider/model the panel defaults to before anything is configured.
DEFAULT_PROVIDER_KEY = "anthropic"
DEFAULT_MODEL_KEY = "claude-opus-4-8"


def iter_catalog_models():
    """Yield ``(provider_key, model_def)`` for every model in the catalog."""
    for provider_key, provider in PROVIDER_CATALOG.items():
        for model in provider.get("models", []):
            yield provider_key, model


def task_preferred_capability(task: str) -> Optional[str]:
    for t in TASK_TYPES:
        if t["id"] == task:
            return t.get("preferred")
    return None
