"""Coverage-focused tests for the Telegram service, AI inference bridge, and
the Telegram API router. These exercise the channel client (mocked httpx), the
command handlers (against the in-memory test DB), preference persistence, and the
HTTP endpoints."""
import pytest

from app.services import telegram as tg


# ---------------------------------------------------------------------------
# httpx test doubles
# ---------------------------------------------------------------------------
class FakeResp:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {"ok": True, "result": {}}
        self.text = text

    def json(self):
        return self._json


class FakeClient:
    """Async context manager whose ``post``/``get`` return queued responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, **kw):
        self.calls.append((url, kw))
        return self._responses.pop(0)

    async def get(self, url, **kw):
        self.calls.append((url, kw))
        return self._responses.pop(0)


def _client_factory(responses):
    """Return a callable usable as ``httpx.AsyncClient(...)`` producing one
    FakeClient per construction (each yields the next queued response)."""
    queue = list(responses)

    def make(*a, **k):
        return FakeClient([queue.pop(0)])

    return make


@pytest.fixture(autouse=True)
def _reset_prefs_cache():
    tg._PREFS_CACHE = None
    tg._chat_state.clear()
    yield
    tg._PREFS_CACHE = None
    tg._chat_state.clear()


@pytest.fixture
def configured_bot(monkeypatch):
    """A TelegramChannel that looks configured (token + chat id)."""
    monkeypatch.setattr(tg.settings, "TELEGRAM_BOT_TOKEN", "T:OKEN", raising=False)
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "111", raising=False)


# ---------------------------------------------------------------------------
# TelegramChannel
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_channel_send_ok(monkeypatch, configured_bot):
    monkeypatch.setattr(tg.httpx, "AsyncClient", _client_factory([FakeResp(200, {"ok": True})]))
    ch = tg.TelegramChannel("T:OKEN", "111")
    res = await ch.send("hello", subject="Hi", silent=True)
    assert res["ok"] is True and res["channel"] == "telegram"


@pytest.mark.asyncio
async def test_channel_send_not_configured():
    ch = tg.TelegramChannel(None, None)
    res = await ch.send("hello")
    assert res["ok"] is False


@pytest.mark.asyncio
async def test_channel_post_markdown_retry(monkeypatch, configured_bot):
    # First call fails with a parse error, retry (without parse_mode) succeeds.
    monkeypatch.setattr(
        tg.httpx, "AsyncClient",
        _client_factory([
            FakeResp(400, text="Bad Request: can't parse entities"),
            FakeResp(200, {"ok": True}),
        ]),
    )
    ch = tg.TelegramChannel("T:OKEN", "111")
    res = await ch._post("sendMessage", {"chat_id": "111", "text": "*x", "parse_mode": "Markdown"})
    assert res.get("ok") is True


@pytest.mark.asyncio
async def test_channel_post_http_error(monkeypatch, configured_bot):
    monkeypatch.setattr(tg.httpx, "AsyncClient", _client_factory([FakeResp(500, text="boom")]))
    ch = tg.TelegramChannel("T:OKEN", "111")
    res = await ch._post("sendMessage", {"chat_id": "111", "text": "x"})
    assert res["ok"] is False and "500" in res["error"]


@pytest.mark.asyncio
async def test_channel_webhook_helpers(monkeypatch, configured_bot):
    monkeypatch.setattr(
        tg.httpx, "AsyncClient",
        _client_factory([FakeResp(200, {"ok": True}) for _ in range(4)]),
    )
    ch = tg.TelegramChannel("T:OKEN", "111")
    assert (await ch.set_webhook("https://x/api/telegram/webhook", secret_token="s")).get("ok")
    assert (await ch.delete_webhook()).get("ok")
    assert (await ch.get_webhook_info()).get("ok")
    assert (await ch.answer_callback("cb1", "done")).get("ok")


@pytest.mark.asyncio
async def test_channel_send_with_menu(monkeypatch, configured_bot):
    monkeypatch.setattr(tg.httpx, "AsyncClient", _client_factory([FakeResp(200, {"ok": True})]))
    ch = tg.TelegramChannel("T:OKEN", "111")
    res = await ch.send_with_menu("menu")
    assert res.get("ok")


def test_channel_webhook_without_token():
    ch = tg.TelegramChannel(None, None)
    import asyncio
    assert asyncio.get_event_loop().run_until_complete(ch.set_webhook("u"))["ok"] is False


# ---------------------------------------------------------------------------
# Service: status / webhook / ensure_webhook / test_send
# ---------------------------------------------------------------------------
def test_get_status_shape():
    tg._PREFS_CACHE = tg.build_default_prefs()
    status = tg.telegram_service.get_status()
    assert "telegram" in status["channels"]
    assert set(status["events_registry"]) == set(tg.EVENT_REGISTRY)
    assert any(g["id"] == "expiry" for g in status["event_groups"])


@pytest.mark.asyncio
async def test_service_webhook_passthrough(monkeypatch, configured_bot):
    monkeypatch.setattr(
        tg.httpx, "AsyncClient",
        _client_factory([FakeResp(200, {"ok": True}) for _ in range(3)]),
    )
    assert (await tg.telegram_service.set_webhook("https://x/api/telegram/webhook")).get("ok")
    assert (await tg.telegram_service.delete_webhook()).get("ok")
    assert (await tg.telegram_service.webhook_info()).get("ok")


@pytest.mark.asyncio
async def test_ensure_webhook_no_public_url(monkeypatch, configured_bot):
    for key in ("BACKEND_PUBLIC_URL", "RENDER_EXTERNAL_URL", "PUBLIC_URL"):
        monkeypatch.delenv(key, raising=False)
    res = await tg.telegram_service.ensure_webhook()
    assert res.get("skipped") == "no_public_url"


@pytest.mark.asyncio
async def test_ensure_webhook_sets_when_url_differs(monkeypatch, configured_bot):
    monkeypatch.setenv("BACKEND_PUBLIC_URL", "https://api.example.com")
    # getWebhookInfo returns a different URL → setWebhook is called.
    monkeypatch.setattr(
        tg.httpx, "AsyncClient",
        _client_factory([
            FakeResp(200, {"ok": True, "result": {"url": "https://old"}}),  # get_webhook_info
            FakeResp(200, {"ok": True}),  # set_webhook
        ]),
    )
    res = await tg.telegram_service.ensure_webhook()
    assert res.get("ok") is True


@pytest.mark.asyncio
async def test_ensure_webhook_skips_when_not_configured(monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_BOT_TOKEN", None, raising=False)
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", None, raising=False)
    res = await tg.telegram_service.ensure_webhook()
    assert res.get("skipped") == "not_configured"


@pytest.mark.asyncio
async def test_test_send_no_channel():
    tg._PREFS_CACHE = tg.build_default_prefs()
    # Nothing configured → no channels ready → empty results.
    results = await tg.telegram_service.test_send()
    assert results == []


# ---------------------------------------------------------------------------
# Preferences persistence (DB-backed)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_prefs_roundtrip(db_session):
    saved = await tg.save_prefs(
        tg._merge_into_defaults({"min_priority": "high"}), db=db_session
    )
    assert saved["min_priority"] == "high"
    tg._PREFS_CACHE = None
    loaded = await tg.load_prefs(db=db_session)
    assert loaded["min_priority"] == "high"
    updated = await tg.update_prefs({"events": {"facility_expiring": False}}, db=db_session)
    assert updated["events"]["facility_expiring"] is False


# ---------------------------------------------------------------------------
# Command handlers (against the in-memory test DB)
# ---------------------------------------------------------------------------
@pytest.fixture
def patched_handlers(db_session, monkeypatch):
    """Point the handlers' AsyncSessionLocal at the test engine and capture
    every outbound Telegram message instead of hitting the network."""
    import app.database as appdb
    from sqlalchemy.ext.asyncio import async_sessionmaker

    maker = async_sessionmaker(bind=db_session.bind, expire_on_commit=False)
    monkeypatch.setattr(appdb, "AsyncSessionLocal", maker)
    monkeypatch.setattr(tg.settings, "TELEGRAM_CHAT_ID", "111", raising=False)
    tg._PREFS_CACHE = tg.build_default_prefs()

    sent = []

    async def _capture_send(self, message, **k):
        sent.append(message)
        return {"ok": True, "channel": "telegram"}

    async def _capture_menu(self, message, **k):
        sent.append(message)
        return {"ok": True}

    monkeypatch.setattr(tg.TelegramChannel, "send", _capture_send)
    monkeypatch.setattr(tg.TelegramChannel, "send_with_menu", _capture_menu)
    return sent


@pytest.mark.asyncio
async def test_cmd_read_only(patched_handlers):
    svc = tg.telegram_service
    await svc._cmd_menu("111")
    await svc._cmd_help("111")
    await svc._cmd_ping("111")
    await svc._cmd_status("111")
    await svc._cmd_stats("111")
    await svc._cmd_expiring("111")
    await svc._cmd_fx("111")
    assert len(patched_handlers) >= 7


@pytest.mark.asyncio
async def test_cmd_scan(patched_handlers):
    res = await tg.telegram_service._cmd_scan("111")
    assert res["handled"] == "scan"
    assert any("اسکن انقضا" in m for m in patched_handlers)


@pytest.mark.asyncio
async def test_cmd_backup_disabled(patched_handlers, monkeypatch):
    monkeypatch.setattr("app.services.drive_sync.is_enabled", lambda: False)
    res = await tg.telegram_service._cmd_backup("111")
    assert res["handled"] == "backup_disabled"


@pytest.mark.asyncio
async def test_cmd_ai_with_answer(patched_handlers, monkeypatch):
    async def _fake_complete(db, prompt, **k):
        return {"ok": True, "text": "پاسخ نمونه", "model": "Test Model"}

    monkeypatch.setattr("app.ai.inference.complete", _fake_complete)
    res = await tg.telegram_service._cmd_ai("111", "سؤال")
    assert res["handled"] == "ai"
    assert any("پاسخ نمونه" in m for m in patched_handlers)


@pytest.mark.asyncio
async def test_cmd_ai_no_model(patched_handlers, monkeypatch):
    async def _fake_complete(db, prompt, **k):
        return {"ok": False, "error": "no_model", "text": ""}

    monkeypatch.setattr("app.ai.inference.complete", _fake_complete)
    await tg.telegram_service._cmd_ai("111", "سؤال")
    assert any("پیکربندی نشده" in m for m in patched_handlers)


@pytest.mark.asyncio
async def test_cmd_ai_empty_prompts_for_question(patched_handlers):
    res = await tg.telegram_service._cmd_ai("111", "")
    assert res["handled"] == "ai_prompt"
    assert tg._get_state("111")["phase"] == "awaiting_ai"


@pytest.mark.asyncio
async def test_dispatch_unknown_command(patched_handlers):
    res = await tg.telegram_service._dispatch_command("111", "/bogus", "")
    assert res["handled"] == "unknown"


@pytest.mark.asyncio
async def test_dispatch_all_known(patched_handlers, monkeypatch):
    monkeypatch.setattr("app.services.drive_sync.is_enabled", lambda: False)
    for cmd in ["/start", "/menu", "/help", "/ping", "/status", "/stats",
                "/expiring", "/fx", "/scan", "/backup"]:
        res = await tg.telegram_service._dispatch_command("111", cmd, "")
        assert res["ok"] is True


@pytest.mark.asyncio
async def test_callback_routes_to_command(patched_handlers, monkeypatch):
    captured = {}

    async def _fake_dispatch(self, chat_id, command, arg):
        captured["command"] = command
        return {"ok": True}

    monkeypatch.setattr(tg.TelegramService, "_dispatch_command", _fake_dispatch)
    await tg.telegram_service.handle_update(
        {"callback_query": {"id": "cb", "data": "status", "message": {"chat": {"id": 111}}}}
    )
    assert captured["command"] == "/status"


@pytest.mark.asyncio
async def test_awaiting_ai_state_consumes_next_text(patched_handlers, monkeypatch):
    async def _fake_complete(db, prompt, **k):
        return {"ok": True, "text": "ok", "model": "M"}

    monkeypatch.setattr("app.ai.inference.complete", _fake_complete)
    tg._set_state("111", "awaiting_ai")
    res = await tg.telegram_service.handle_update(
        {"message": {"text": "موجودی چقدر است", "chat": {"id": 111}}}
    )
    assert res["handled"] == "ai"


# ---------------------------------------------------------------------------
# AI inference bridge
# ---------------------------------------------------------------------------
def _resolved(provider_key="anthropic", base_url="https://api.anthropic.com", auth="api_key"):
    from app.ai.manager import ResolvedModel

    return ResolvedModel(
        task="chat", provider_key=provider_key, model_key="m-1",
        display_name="Test Model", api_key="sk-test", auth_scheme=auth,
        base_url=base_url, capabilities=["text"], temperature=0.3,
    )


@pytest.mark.asyncio
async def test_inference_no_model(monkeypatch):
    from app.ai import inference

    async def _none(db, task):
        return None

    monkeypatch.setattr(inference.ai_manager, "resolve", _none)
    res = await inference.complete(None, "hi")
    assert res["ok"] is False and res["error"] == "no_model"


@pytest.mark.asyncio
async def test_inference_anthropic(monkeypatch):
    from app.ai import inference

    async def _resolve(db, task):
        return _resolved("anthropic")

    monkeypatch.setattr(inference.ai_manager, "resolve", _resolve)
    monkeypatch.setattr(
        inference.httpx, "AsyncClient",
        _client_factory([FakeResp(200, {"content": [{"type": "text", "text": "salam"}]})]),
    )
    res = await inference.complete(None, "hi", system="sys")
    assert res["ok"] is True and res["text"] == "salam" and res["model"] == "Test Model"


@pytest.mark.asyncio
async def test_inference_openai(monkeypatch):
    from app.ai import inference

    async def _resolve(db, task):
        return _resolved("openai", "https://api.openai.com/v1")

    monkeypatch.setattr(inference.ai_manager, "resolve", _resolve)
    monkeypatch.setattr(
        inference.httpx, "AsyncClient",
        _client_factory([FakeResp(200, {"choices": [{"message": {"content": "hi there"}}]})]),
    )
    res = await inference.complete(None, "hi", system="sys")
    assert res["ok"] is True and res["text"] == "hi there"


@pytest.mark.asyncio
async def test_inference_gemini(monkeypatch):
    from app.ai import inference

    async def _resolve(db, task):
        return _resolved("gemini", "https://generativelanguage.googleapis.com")

    monkeypatch.setattr(inference.ai_manager, "resolve", _resolve)
    monkeypatch.setattr(
        inference.httpx, "AsyncClient",
        _client_factory([FakeResp(200, {"candidates": [{"content": {"parts": [{"text": "g"}]}}]})]),
    )
    res = await inference.complete(None, "hi", system="sys")
    assert res["ok"] is True and res["text"] == "g"


@pytest.mark.asyncio
async def test_inference_provider_error(monkeypatch):
    from app.ai import inference

    async def _resolve(db, task):
        return _resolved("openai", "https://api.openai.com/v1")

    monkeypatch.setattr(inference.ai_manager, "resolve", _resolve)
    monkeypatch.setattr(
        inference.httpx, "AsyncClient",
        _client_factory([FakeResp(401, {"error": {"message": "bad key"}}, text="bad key")]),
    )
    res = await inference.complete(None, "hi")
    assert res["ok"] is False and "401" in res["error"]


# ---------------------------------------------------------------------------
# API router
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_router_status(client, auth_headers):
    r = await client.get("/api/telegram/status", headers=auth_headers)
    assert r.status_code == 200
    assert "events_registry" in r.json()


@pytest.mark.asyncio
async def test_router_prefs_admin_only(client, auth_headers, admin_headers):
    # Non-admin is rejected.
    r = await client.put("/api/telegram/prefs", json={"min_priority": "high"}, headers=auth_headers)
    assert r.status_code == 403
    # Admin succeeds.
    r = await client.put("/api/telegram/prefs", json={"min_priority": "high"}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["prefs"]["min_priority"] == "high"


@pytest.mark.asyncio
async def test_router_prefs_bad_priority(client, admin_headers):
    r = await client.put("/api/telegram/prefs", json={"min_priority": "nope"}, headers=admin_headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_router_test_send(client, admin_headers):
    r = await client.post("/api/telegram/test", headers=admin_headers)
    assert r.status_code == 200  # ok False (nothing configured) but 200


@pytest.mark.asyncio
async def test_router_webhook_secret_mismatch(client, monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_WEBHOOK_SECRET", "s3cret", raising=False)
    r = await client.post(
        "/api/telegram/webhook",
        json={"message": {"text": "/status", "chat": {"id": 1}}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert r.status_code == 200 and r.json().get("ignored") is True


@pytest.mark.asyncio
async def test_router_webhook_dispatches(client, monkeypatch):
    monkeypatch.setattr(tg.settings, "TELEGRAM_WEBHOOK_SECRET", None, raising=False)
    captured = {}

    async def _fake_handle(body):
        captured["body"] = body
        return {"ok": True, "handled": "x"}

    monkeypatch.setattr(tg.telegram_service, "handle_update", _fake_handle)
    r = await client.post("/api/telegram/webhook", json={"message": {"text": "hi"}})
    assert r.status_code == 200 and captured["body"]["message"]["text"] == "hi"


@pytest.mark.asyncio
async def test_router_set_delete_webhook(client, admin_headers):
    # Bot token unset → channel methods early-return {ok:False}; endpoints still 200.
    r = await client.post(
        "/api/telegram/set-webhook", json={"webhook_url": "https://x/api/telegram/webhook"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    r = await client.post("/api/telegram/delete-webhook", headers=admin_headers)
    assert r.status_code == 200
