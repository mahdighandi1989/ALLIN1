"""Central AI infrastructure for the panel.

Everything that uses an AI model roots here:

* :mod:`app.ai.catalog`  — the static, code-defined catalog of providers, models,
                           capabilities, and application task types. Seed data.
* :mod:`app.ai.manager`  — :class:`AIManager`, the single entry point consumers
                           call to resolve a task to a configured model and its
                           credentials. Wire new AI features to ``ai_manager``.

Typical use from any service/router::

    from app.ai import ai_manager, AITask

    resolved = await ai_manager.resolve(db, AITask.DOCUMENT_EXTRACTION)
    if resolved:
        # resolved.provider_key / resolved.model_key / resolved.api_key / ...
        ...
"""
from app.ai.catalog import (
    AITask,
    Capability,
    PROVIDER_CATALOG,
    TASK_TYPES,
    CAPABILITIES,
)
from app.ai.manager import AIManager, ResolvedModel, ai_manager

__all__ = [
    "AITask",
    "Capability",
    "PROVIDER_CATALOG",
    "TASK_TYPES",
    "CAPABILITIES",
    "AIManager",
    "ResolvedModel",
    "ai_manager",
]
