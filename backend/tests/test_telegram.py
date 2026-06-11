"""Tests for the two-way Telegram integration service."""
import pytest

from app.services import telegram as tg


@pytest.fixture(autouse=True)
def _reset_prefs_cache():
    """The prefs cache is a process-global; isolate it between tests."""
    tg._PREFS_CACHE = None
    tg._chat_state.clear()
    yield
    tg._PREFS_CACHE = None
    tg._chat_state.clear()


def test_default_prefs_cover_every_event():
    prefs = tg.build_default_prefs()
    assert set(prefs["events"]) == set(tg.EVENT_REGISTRY)
    assert set(prefs["sound"]) == set(tg.EVENT_REGISTRY)
    assert prefs["min_priority"] == "low"
    assert prefs["channels"]["telegram"]["enabled"] is True


def test_merge_backfills_newly_added_events():
    # A stored blob missing a known event should be backfilled from the registry.
    stored = {"events": {"facility_expiring": False}}
    merged = tg._merge_into_defaults(stored)
    assert merged["events"]["facility_expiring"] is False  # user choice preserved
    # Every other registry event is still present with its default.
    for ev, meta in tg.EVENT_REGISTRY.items():
        assert ev in merged["events"]
        assert ev in merged["sound"]


def test_allow_list_union_of_env_and_prefs(monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "111, 222", raising=False)
    tg._PREFS_CACHE = tg._merge_into_defaults({"allowed_chat_ids": ["333"]})
    ids = tg.allowed_chat_ids()
    assert ids == ["111", "222", "333"]
    assert tg.is_allowed("222") is True
    assert tg.is_allowed("999") is False


def test_is_allowed_false_when_no_list(monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "", raising=False)
    tg._PREFS_CACHE = tg.build_default_prefs()
    assert tg.allowed_chat_ids() == []
    assert tg.is_allowed("123") is False


@pytest.mark.asyncio
async def test_notify_event_skips_disabled(monkeypatch):
    # Disable an event in the cache; no channel send should be attempted.
    tg._PREFS_CACHE = tg._merge_into_defaults({"events": {"facility_expiring": False}})
    monkeypatch.setattr(tg.TelegramChannel, "is_configured", lambda self: True)

    called = {"n": 0}

    async def _fake_send(self, *a, **k):
        called["n"] += 1
        return {"ok": True, "channel": "telegram"}

    monkeypatch.setattr(tg.TelegramChannel, "send", _fake_send)
    results = await tg.telegram_service.notify_event("facility_expiring", "x", priority="high")
    assert results == []
    assert called["n"] == 0


@pytest.mark.asyncio
async def test_notify_event_respects_min_priority(monkeypatch):
    tg._PREFS_CACHE = tg._merge_into_defaults({"min_priority": "high"})
    monkeypatch.setattr(tg.TelegramChannel, "is_configured", lambda self: True)

    async def _fake_send(self, *a, **k):
        return {"ok": True, "channel": "telegram"}

    monkeypatch.setattr(tg.TelegramChannel, "send", _fake_send)
    # offer_letter_created at medium priority is below the min — suppressed.
    low = await tg.telegram_service.notify_event("offer_letter_created", "x", priority="medium")
    assert low == []
    # A high-priority send goes through.
    high = await tg.telegram_service.notify_event("facility_expiring", "x", priority="high")
    assert any(r.get("ok") for r in high)


@pytest.mark.asyncio
async def test_notify_event_silent_follows_sound_pref(monkeypatch):
    tg._PREFS_CACHE = tg._merge_into_defaults(
        {"events": {"facility_expiring": True}, "sound": {"facility_expiring": False}}
    )
    monkeypatch.setattr(tg.TelegramChannel, "is_configured", lambda self: True)
    captured = {}

    async def _fake_send(self, message, **k):
        captured.update(k)
        return {"ok": True, "channel": "telegram", "silent": k.get("silent")}

    monkeypatch.setattr(tg.TelegramChannel, "send", _fake_send)
    await tg.telegram_service.notify_event("facility_expiring", "x", priority="high")
    assert captured.get("silent") is True  # sound off -> delivered silently


@pytest.mark.asyncio
async def test_handle_update_bootstrap_returns_chat_id(monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "", raising=False)
    tg._PREFS_CACHE = tg.build_default_prefs()
    sent = {}

    async def _fake_send(self, message, **k):
        sent["msg"] = message
        sent["chat_id"] = k.get("chat_id")
        return {"ok": True}

    monkeypatch.setattr(tg.TelegramChannel, "send", _fake_send)
    res = await tg.telegram_service.handle_update(
        {"message": {"text": "سلام", "chat": {"id": 4242}}}
    )
    assert res.get("handled") == "bootstrap"
    assert "4242" in sent["msg"]


@pytest.mark.asyncio
async def test_handle_update_ignores_unlisted_chat(monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "111", raising=False)
    tg._PREFS_CACHE = tg.build_default_prefs()

    async def _boom(self, *a, **k):  # should never be called
        raise AssertionError("must not send to an unlisted chat")

    monkeypatch.setattr(tg.TelegramChannel, "send", _boom)
    res = await tg.telegram_service.handle_update(
        {"message": {"text": "/status", "chat": {"id": 999}}}
    )
    assert res.get("ignored") is True


@pytest.mark.asyncio
async def test_free_text_routes_to_ai(monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "111", raising=False)
    tg._PREFS_CACHE = tg.build_default_prefs()
    routed = {}

    async def _fake_ai(self, chat_id, question):
        routed["q"] = question
        return {"ok": True, "handled": "ai"}

    monkeypatch.setattr(tg.TelegramService, "_cmd_ai", _fake_ai)
    res = await tg.telegram_service.handle_update(
        {"message": {"text": "وضعیت پرتفوی چطور است؟", "chat": {"id": 111}}}
    )
    assert res.get("handled") == "ai"
    assert routed["q"] == "وضعیت پرتفوی چطور است؟"


@pytest.mark.asyncio
async def test_menu_alias_maps_to_command(monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "111", raising=False)
    tg._PREFS_CACHE = tg.build_default_prefs()
    dispatched = {}

    async def _fake_dispatch(self, chat_id, command, arg):
        dispatched["command"] = command
        return {"ok": True}

    monkeypatch.setattr(tg.TelegramService, "_dispatch_command", _fake_dispatch)
    await tg.telegram_service.handle_update(
        {"message": {"text": "📊 وضعیت", "chat": {"id": 111}}}
    )
    assert dispatched["command"] == "/status"
