"""The central AI manager — the single entry point for using AI in the panel.

Every AI feature roots here instead of hardcoding a provider/model. A consumer
asks the manager to resolve an application task (e.g. ``AITask.CHAT``) and gets
back a :class:`ResolvedModel` carrying the model id, provider, credentials, base
URL, and default params — or ``None`` when nothing is configured yet. The
manager honours the DB control layer at every step: provider enabled + has a key
(DB or env), model enabled, and the task's route (or, with no route, the best
enabled model for the task's preferred capability).

This file deliberately does **not** make HTTP calls to any provider. It is the
wiring/switchboard. When a feature needs to actually call a model, it resolves
here first, then uses the returned credentials with the appropriate SDK.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import catalog
from app.models.ai_config import AIModel, AIProvider, AITaskRoute

logger = logging.getLogger(__name__)


@dataclass
class ResolvedModel:
    """A fully-resolved, ready-to-use model selection for a task.

    ``api_key`` is the effective key (DB value, else the provider's env var).
    Treat this object as a secret — it is only ever produced server-side and is
    never serialized to the client.
    """

    task: str
    provider_key: str
    model_key: str
    display_name: str
    api_key: Optional[str]
    base_url: Optional[str]
    capabilities: List[str] = field(default_factory=list)
    max_output_tokens: Optional[int] = None
    temperature: Optional[float] = None
    context_window: Optional[int] = None

    @property
    def is_usable(self) -> bool:
        """True when we have everything needed to actually call the provider."""
        return bool(self.api_key)


class AIManager:
    """Resolves application tasks to configured models. Stateless; safe to share."""

    # -- credential helpers -------------------------------------------------
    @staticmethod
    def effective_api_key(provider: AIProvider) -> Optional[str]:
        """The key to use: explicit DB value, else the provider's env var."""
        if provider.api_key:
            return provider.api_key
        if provider.env_key:
            return os.getenv(provider.env_key) or None
        return None

    @classmethod
    def provider_configured(cls, provider: AIProvider) -> bool:
        return bool(cls.effective_api_key(provider))

    # -- core resolution ----------------------------------------------------
    async def resolve(self, db: AsyncSession, task: str) -> Optional[ResolvedModel]:
        """Resolve ``task`` to a usable model, or ``None`` if none is configured.

        Order of preference:
          1. The model explicitly routed to this task (if its route is enabled).
          2. The highest-priority enabled model whose provider is configured and
             that supports the task's preferred capability.
          3. The highest-priority enabled, configured model of any kind.
        """
        providers = {p.key: p for p in (await db.execute(select(AIProvider))).scalars()}

        # 1. Explicit route.
        route = await db.get(AITaskRoute, task)
        if route and route.enabled and route.model_id is not None:
            model = await db.get(AIModel, route.model_id)
            resolved = self._try_build(model, providers, task)
            if resolved:
                return resolved
            logger.debug("AI route for %s points at an unusable model; falling back", task)

        # 2 & 3. Best enabled+configured model, preferring the task's capability.
        preferred_cap = catalog.task_preferred_capability(task)
        models = (
            await db.execute(
                select(AIModel).where(AIModel.enabled.is_(True)).order_by(AIModel.priority)
            )
        ).scalars().all()

        fallback: Optional[ResolvedModel] = None
        for model in models:
            resolved = self._try_build(model, providers, task)
            if not resolved:
                continue
            if preferred_cap and preferred_cap in resolved.capabilities:
                return resolved
            if fallback is None:
                fallback = resolved
        return fallback

    def _try_build(
        self,
        model: Optional[AIModel],
        providers: Dict[str, AIProvider],
        task: str,
    ) -> Optional[ResolvedModel]:
        if model is None or not model.enabled:
            return None
        provider = providers.get(model.provider_key)
        if provider is None or not provider.enabled:
            return None
        api_key = self.effective_api_key(provider)
        if not api_key:
            return None
        base_url = provider.base_url or catalog.PROVIDER_CATALOG.get(
            provider.key, {}
        ).get("base_url")
        return ResolvedModel(
            task=task,
            provider_key=provider.key,
            model_key=model.model_key,
            display_name=model.display_name,
            api_key=api_key,
            base_url=base_url,
            capabilities=list(model.capabilities or []),
            max_output_tokens=model.max_output_tokens,
            temperature=model.temperature,
            context_window=model.context_window,
        )

    async def is_available(self, db: AsyncSession, task: Optional[str] = None) -> bool:
        """True if at least one usable model exists (optionally for ``task``)."""
        if task is not None:
            return (await self.resolve(db, task)) is not None
        for t in catalog.TASK_TYPES:
            if await self.resolve(db, t["id"]) is not None:
                return True
        return False

    async def status(self, db: AsyncSession) -> Dict[str, Any]:
        """A small summary for the Settings header / health checks."""
        providers = (await db.execute(select(AIProvider))).scalars().all()
        configured = [p.key for p in providers if p.enabled and self.provider_configured(p)]
        enabled_models = (
            await db.execute(
                select(AIModel).where(AIModel.enabled.is_(True))
            )
        ).scalars().all()
        usable_models = [
            m for m in enabled_models
            if any(p.key == m.provider_key and p.enabled and self.provider_configured(p)
                   for p in providers)
        ]
        return {
            "configured_providers": configured,
            "usable_model_count": len(usable_models),
            "any_available": bool(usable_models),
        }


# A module-level singleton consumers import: ``from app.ai import ai_manager``.
ai_manager = AIManager()


# ---------------------------------------------------------------------------
# Seeding — copy the static catalog into the DB on first run, idempotently.
# Called from the startup schema bootstrap. Never overwrites admin choices
# (enabled flags, keys, custom models) — only fills in what's missing and keeps
# catalog metadata (display name, capabilities, pricing) fresh.
# ---------------------------------------------------------------------------
async def seed_ai_catalog(db: AsyncSession) -> Dict[str, int]:
    """Ensure provider/model/route rows exist for the catalog. Idempotent."""
    counts = {"providers": 0, "models": 0, "routes": 0}

    existing_providers = {
        p.key: p for p in (await db.execute(select(AIProvider))).scalars()
    }
    for key, pdef in catalog.PROVIDER_CATALOG.items():
        provider = existing_providers.get(key)
        if provider is None:
            provider = AIProvider(
                key=key,
                display_name=pdef["display_name"],
                enabled=False,  # off until an admin adds a key
                base_url=pdef.get("base_url"),
                env_key=pdef.get("env_key"),
                notes=pdef.get("notes"),
            )
            db.add(provider)
            counts["providers"] += 1
        else:
            # Refresh non-destructive metadata (keep enabled flag, key, base_url override).
            provider.display_name = pdef["display_name"]
            provider.env_key = pdef.get("env_key")
            if not provider.notes:
                provider.notes = pdef.get("notes")

    existing_models = {
        m.model_key: m for m in (await db.execute(select(AIModel))).scalars()
    }
    for provider_key, mdef in catalog.iter_catalog_models():
        model = existing_models.get(mdef["model_key"])
        if model is None:
            db.add(
                AIModel(
                    model_key=mdef["model_key"],
                    provider_key=provider_key,
                    display_name=mdef.get("display_name", mdef["model_key"]),
                    enabled=True,
                    capabilities=list(mdef.get("capabilities", [])),
                    max_output_tokens=mdef.get("max_output_tokens"),
                    context_window=mdef.get("context_window"),
                    priority=mdef.get("priority", 5),
                    input_cost_per_1m=mdef.get("input_cost_per_1m"),
                    output_cost_per_1m=mdef.get("output_cost_per_1m"),
                    is_custom=False,
                )
            )
            counts["models"] += 1
        elif not model.is_custom:
            # Keep catalog metadata current; preserve the admin's enabled flag.
            model.display_name = mdef.get("display_name", model.display_name)
            model.provider_key = provider_key
            model.capabilities = list(mdef.get("capabilities", []))
            model.max_output_tokens = mdef.get("max_output_tokens")
            model.context_window = mdef.get("context_window")
            model.input_cost_per_1m = mdef.get("input_cost_per_1m")
            model.output_cost_per_1m = mdef.get("output_cost_per_1m")

    # Make sure a route row exists for every task (unrouted = auto-pick).
    existing_routes = {
        r.task: r for r in (await db.execute(select(AITaskRoute))).scalars()
    }
    for t in catalog.TASK_TYPES:
        if t["id"] not in existing_routes:
            db.add(AITaskRoute(task=t["id"], model_id=None, enabled=True))
            counts["routes"] += 1

    await db.commit()
    if any(counts.values()):
        logger.info("AI catalog seeded: %s", counts)
    return counts
