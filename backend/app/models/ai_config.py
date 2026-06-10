"""AI providers, models, and task routing — the persisted control layer for AI.

This is the single source of truth for *which* AI providers and models the panel
may use, and *where* each one is wired in. Everything is editable from the
Settings page and takes effect immediately; nothing here calls a provider on its
own. Consumers never hardcode a model — they ask :mod:`app.ai.manager` to resolve
a task to a configured model, and the answer is rooted in these three tables:

* ``ai_providers``    — one row per provider (Anthropic, OpenAI, …): enabled flag,
                        API key (secret), optional base-URL override.
* ``ai_models``       — the catalog of models (seeded) plus any custom models the
                        admin adds: capabilities, default params, enabled flag.
* ``ai_task_routes``  — maps an application task ("chat", "document_extraction",
                        …) to the model that should serve it. This is the wiring:
                        change a route here and every consumer of that task
                        follows, without touching code.

The rows are seeded from :mod:`app.ai.catalog` on first run and kept in sync by
the self-healing schema bootstrap, so the panel works out of the box (disabled,
awaiting an API key) and an admin only has to flip a switch and paste a key.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database import Base

# Use JSONB on Postgres and plain JSON elsewhere (SQLite in tests).
JSONType = JSON().with_variant(JSONB(), "postgresql")


def _mask_secret(value: Optional[str]) -> Optional[str]:
    """Never return a raw API key to the client — show only the last 4 chars."""
    if not value:
        return None
    return ("•" * 4 + value[-4:]) if len(value) > 4 else "••••"


class AIProvider(Base):
    """A configured AI provider (Anthropic, OpenAI, Gemini, …)."""

    __tablename__ = "ai_providers"

    key = Column(String(40), primary_key=True)            # "anthropic", "openai", …
    display_name = Column(String(80), nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    # Secret. Stored as text, never returned raw (see to_dict). If blank, the
    # manager falls back to the provider's env var (e.g. ANTHROPIC_API_KEY).
    api_key = Column(Text, nullable=True)
    # Optional override for the provider's API base URL (proxies, gateways).
    base_url = Column(String(255), nullable=True)
    # Env var the manager reads when api_key is blank (informational for the UI).
    env_key = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self, *, env_configured: bool = False) -> Dict[str, Any]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "enabled": bool(self.enabled),
            "has_api_key": bool(self.api_key),
            "api_key_masked": _mask_secret(self.api_key),
            "base_url": self.base_url,
            "env_key": self.env_key,
            # True when a key is set in the DB *or* available from the environment.
            "configured": bool(self.api_key) or env_configured,
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AIModel(Base):
    """A single AI model the panel may use (seeded catalog entry or custom)."""

    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # The provider's model id, e.g. "claude-opus-4-8". Unique per install.
    model_key = Column(String(120), unique=True, index=True, nullable=False)
    provider_key = Column(String(40), ForeignKey("ai_providers.key"), nullable=False, index=True)
    display_name = Column(String(120), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    # What the model can do — a list of capability ids (see catalog.CAPABILITIES).
    capabilities = Column(JSONType, default=list)

    # Sensible request defaults a consumer can pick up from the resolved model.
    max_output_tokens = Column(Integer, nullable=True)
    context_window = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    # Lower = preferred when several models could serve the same task/capability.
    priority = Column(Integer, default=5, nullable=False)

    # Pricing (USD per 1M tokens) — informational, for the UI and cost estimates.
    input_cost_per_1m = Column(Float, nullable=True)
    output_cost_per_1m = Column(Float, nullable=True)

    # True for admin-added models (kept across re-seeds; catalog entries are
    # refreshed). Lets the UI offer "delete" only for custom rows.
    is_custom = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "model_key": self.model_key,
            "provider_key": self.provider_key,
            "display_name": self.display_name,
            "enabled": bool(self.enabled),
            "capabilities": list(self.capabilities or []),
            "max_output_tokens": self.max_output_tokens,
            "context_window": self.context_window,
            "temperature": self.temperature,
            "priority": self.priority,
            "input_cost_per_1m": self.input_cost_per_1m,
            "output_cost_per_1m": self.output_cost_per_1m,
            "is_custom": bool(self.is_custom),
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AITaskRoute(Base):
    """Maps an application task to the model that should serve it.

    This is the wiring layer: a consumer asks the manager for task "chat" and
    gets whatever model is routed here (or, if unset, the highest-priority
    enabled model that supports the task's capability). Editing a route re-aims
    every consumer of that task at once.
    """

    __tablename__ = "ai_task_routes"

    task = Column(String(60), primary_key=True)           # "chat", "document_extraction", …
    model_id = Column(Integer, ForeignKey("ai_models.id", ondelete="SET NULL"), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "model_id": self.model_id,
            "enabled": bool(self.enabled),
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# Pydantic request/response schemas (used by the router)
# ---------------------------------------------------------------------------
class ProviderUpdate(BaseModel):
    enabled: Optional[bool] = None
    # Send a new key to set it; send "" to clear it; omit to leave unchanged.
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    notes: Optional[str] = None


class ModelCreate(BaseModel):
    model_key: str
    provider_key: str
    display_name: Optional[str] = None
    capabilities: List[str] = []
    max_output_tokens: Optional[int] = None
    context_window: Optional[int] = None
    temperature: Optional[float] = None
    priority: int = 5
    input_cost_per_1m: Optional[float] = None
    output_cost_per_1m: Optional[float] = None
    notes: Optional[str] = None


class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    enabled: Optional[bool] = None
    capabilities: Optional[List[str]] = None
    max_output_tokens: Optional[int] = None
    context_window: Optional[int] = None
    temperature: Optional[float] = None
    priority: Optional[int] = None
    input_cost_per_1m: Optional[float] = None
    output_cost_per_1m: Optional[float] = None
    notes: Optional[str] = None


class TaskRouteUpdate(BaseModel):
    model_id: Optional[int] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = None
