"""The AI model list refreshes itself — nobody has to press «sync»."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.ai import model_sync
from app.models.ai_config import AIModel, AIProvider, AITaskRoute


async def test_overdue_when_never_run(db_session):
    assert await model_sync.seconds_until_due(db_session, 86400) == 0.0


async def test_schedule_survives_a_restart(db_session):
    """The marker is persisted, so a fresh process asks «how long since the last run»."""
    await model_sync._write_marker(db_session, {"at": datetime.now(timezone.utc).isoformat(), "results": {}})
    assert await model_sync.seconds_until_due(db_session, 86400) > 80000
    old = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    await model_sync._write_marker(db_session, {"at": old, "results": {}})
    assert await model_sync.seconds_until_due(db_session, 86400) == 0.0


async def test_sync_all_skips_providers_without_a_key_and_records_the_run(db_session, monkeypatch):
    from app.ai import tester

    db_session.add(AIProvider(key="p-nokey", display_name="No key", enabled=True))
    await db_session.commit()
    called = []

    async def fake(db, key):
        called.append(key)
        return {"ok": True, "added": 1, "removed": 0, "total": 1, "message": "x"}

    monkeypatch.setattr(tester, "sync_provider_models", fake)
    out = await model_sync.sync_all_providers(db_session)
    assert called == []  # nothing to ask without a key
    st = await model_sync.status(db_session)
    assert st["last_run_at"] == out["at"]
    assert st["interval_hours"] >= 1


async def test_delisted_model_detaches_its_route_instead_of_dangling(db_session, monkeypatch):
    from app.ai import tester

    db_session.add(AIProvider(key="px", display_name="PX", enabled=True, base_url="http://x"))
    m_keep = AIModel(model_key="px:keep", api_model_id="keep", provider_key="px", display_name="Keep",
                     enabled=True, capabilities=["text"], priority=5, source="discovered", is_custom=False)
    m_gone = AIModel(model_key="px:gone", api_model_id="gone", provider_key="px", display_name="Gone",
                     enabled=True, capabilities=["text"], priority=5, source="discovered", is_custom=False)
    db_session.add_all([m_keep, m_gone])
    await db_session.commit()
    db_session.add(AITaskRoute(task="chat", model_id=m_gone.id))
    await db_session.commit()

    monkeypatch.setattr(tester.ai_manager, "effective_api_key", staticmethod(lambda p: "k"))

    async def live(*a, **k):
        return [("keep", "Keep"), ("fresh", "Fresh")]

    monkeypatch.setattr(tester, "_fetch_live_models", live)
    r = await tester.sync_provider_models(db_session, "px")
    assert r["ok"] and r["added"] == 1 and r["removed"] == 1
    from sqlalchemy import select
    route = (await db_session.execute(select(AITaskRoute).where(AITaskRoute.task == "chat"))).scalar_one()
    assert route.model_id is None


def _mk(api_id, prio, source="discovered", provider="claude_subscription"):
    return AIModel(model_key=f"{provider}:{api_id}", api_model_id=api_id, provider_key=provider,
                   display_name=api_id, enabled=True, capabilities=["text"], priority=prio,
                   source=source, is_custom=(source == "custom"))


def test_newest_model_outranks_older_hand_ranked_sibling():
    from app.ai.tester import rank_newest_first

    old = _mk("claude-opus-4-8", 1)
    n55, n5 = _mk("claude-opus-5-5", 5), _mk("claude-opus-5", 5)
    older = _mk("claude-opus-4-6", 5)
    son = _mk("claude-sonnet-5-5", 5)
    custom = _mk("claude-opus-9", 5, source="custom")
    pre = _mk("claude-opus-6-preview", 5)
    assert rank_newest_first([old, n55, n5, older, son, custom, pre]) == 2
    assert n55.priority < n5.priority < old.priority
    assert older.priority == 5 and son.priority == 5   # no ranked sonnet anchor
    assert custom.priority == 5 and pre.priority == 5
    assert rank_newest_first([old, n55, n5, older]) == 0   # idempotent


def test_gemini_versions_rank_within_tier():
    from app.ai.tester import rank_newest_first

    old = _mk("gemini-2.0-flash", 3, provider="gemini")
    new = _mk("gemini-2.5-flash", 5, provider="gemini")
    pro = _mk("gemini-2.5-pro", 5, provider="gemini")
    rank_newest_first([old, new, pro])
    assert new.priority < old.priority and pro.priority == 5
