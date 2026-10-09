"""Scheduled, unattended refresh of the AI model list.

Until now the model list only changed when an admin pressed «sync» in Settings.
This loop does that on its own: every ``AI_MODEL_SYNC_HOURS`` (default 24) it
asks each configured provider for its live model list and reconciles it into the
DB (``tester.sync_provider_models`` — adds new models with heuristic
capabilities, refreshes names, drops models the provider delisted, never touches
admin-added custom models).

The schedule survives restarts the same way the Drive snapshot does: the last
run is persisted in ``system_settings`` and the loop asks «how long since the
last run?» rather than «how long since boot?».
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select

logger = logging.getLogger(__name__)

MARKER_KEY = "ai_model_sync_last"


def interval_hours() -> int:
    try:
        return max(1, int(os.getenv("AI_MODEL_SYNC_HOURS", "24")))
    except ValueError:
        return 24


async def _read_marker(db) -> Optional[Dict[str, Any]]:
    from app.models.system_setting import SystemSetting

    row = (await db.execute(select(SystemSetting).where(SystemSetting.key == MARKER_KEY))).scalar_one_or_none()
    if row is None or not (row.value or "").strip():
        return None
    try:
        data = json.loads(row.value)
        return data if isinstance(data, dict) else None
    except ValueError:
        return None


async def _write_marker(db, payload: Dict[str, Any]) -> None:
    from app.models.system_setting import SystemSetting

    value = json.dumps(payload, ensure_ascii=False)
    row = (await db.execute(select(SystemSetting).where(SystemSetting.key == MARKER_KEY))).scalar_one_or_none()
    if row:
        row.value = value
    else:
        db.add(SystemSetting(key=MARKER_KEY, value=value))
    await db.commit()


async def seconds_until_due(db, interval_s: int) -> float:
    """0 (or less) means «now». A missing/unreadable marker means overdue."""
    marker = await _read_marker(db)
    if not marker or not marker.get("at"):
        return 0.0
    try:
        last = datetime.fromisoformat(str(marker["at"]).replace("Z", "+00:00"))
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.0
    return max(0.0, interval_s - (datetime.now(timezone.utc) - last).total_seconds())


async def keyed_provider_lacks_discovered(db) -> bool:
    """True when a provider with a key has no live-discovered model in the DB —
    i.e. the list is showing only the static catalog and a sync is overdue
    regardless of the marker."""
    from app.ai import ai_manager
    from app.models.ai_config import AIModel, AIProvider

    providers = (await db.execute(select(AIProvider))).scalars().all()
    models = (await db.execute(select(AIModel))).scalars().all()
    have = {m.provider_key for m in models if (m.source or "catalog") == "discovered"}
    return any(ai_manager.effective_api_key(p) and p.key not in have for p in providers)


async def sync_all_providers(db) -> Dict[str, Any]:
    """Sync every provider that has a usable key. Never raises."""
    from app.ai import ai_manager
    from app.ai.tester import sync_provider_models
    from app.models.ai_config import AIProvider

    results: Dict[str, Any] = {}
    providers = (await db.execute(select(AIProvider))).scalars().all()
    for p in providers:
        if not ai_manager.effective_api_key(p):
            continue  # no key/token configured — nothing to ask
        try:
            r = await sync_provider_models(db, p.key)
        except Exception as exc:  # noqa: BLE001 - one provider must not stop the rest
            r = {"ok": False, "message": str(exc)[:200]}
        results[p.key] = {k: r.get(k) for k in ("ok", "added", "removed", "total", "message")}
    payload = {"at": datetime.now(timezone.utc).isoformat(), "results": results}
    await _write_marker(db, payload)
    return payload


async def status(db) -> Dict[str, Any]:
    """What the UI shows: when the list was last refreshed, and how often."""
    marker = await _read_marker(db) or {}
    return {"interval_hours": interval_hours(), "last_run_at": marker.get("at"),
            "last_results": marker.get("results") or {}}


async def run_periodic_model_sync() -> None:
    from app.database import AsyncSessionLocal

    interval = interval_hours() * 3600
    settle = max(30, int(os.getenv("AI_MODEL_SYNC_SETTLE_SECONDS", "300")))
    logger.info("AI model auto-sync started (every %sh)", interval_hours())
    try:
        await asyncio.sleep(settle)  # stay clear of the startup memory window
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    due_in = await seconds_until_due(session, interval)
                    if due_in > 0 and await keyed_provider_lacks_discovered(session):
                        due_in = 0  # list was reset (restart/deploy) — don't wait out the interval
                if due_in > 0:
                    await asyncio.sleep(min(due_in, interval))
                    continue
                async with AsyncSessionLocal() as session:
                    payload = await sync_all_providers(session)
                logger.info("AI model auto-sync done: %s", payload.get("results"))
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                logger.error("AI model auto-sync iteration failed: %s", exc)
                await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("AI model auto-sync stopped")
        raise
