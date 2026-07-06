"""A model that rejects `temperature` with a 400 must not force the user to a
weaker model — inference.complete strips the param and retries once."""
import pytest

from app.ai import inference
from app.models.ai_config import AIProvider, AIModel


def test_helpers_detect_and_strip_temperature():
    assert inference._has_temperature({"temperature": 0.2}) is True
    assert inference._has_temperature({"generationConfig": {"temperature": 0}}) is True
    assert inference._has_temperature({"max_tokens": 10}) is False
    p = {"temperature": 0.2, "generationConfig": {"temperature": 0, "maxOutputTokens": 1}}
    inference._strip_temperature(p)
    assert "temperature" not in p and "temperature" not in p["generationConfig"]


class _Resp:
    def __init__(self, status, json_data=None, text=""):
        self.status_code = status
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


class _Client:
    """Fake httpx.AsyncClient: 400 on the call carrying temperature, 200 without."""
    payloads = []

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None):
        _Client.payloads.append(dict(json or {}))
        if inference._has_temperature(json or {}):
            return _Resp(400, text="400: `temperature` is deprecated for this model")
        return _Resp(200, {"content": [{"type": "text", "text": "hello"}]})


async def test_complete_retries_without_temperature(db_session, monkeypatch):
    db_session.add(AIProvider(key="anthropic", display_name="Anthropic", enabled=True,
                              auth_scheme="api_key", base_url="https://api.anthropic.com",
                              api_key="sk-test"))
    db_session.add(AIModel(model_key="claude-opus-4-8", provider_key="anthropic",
                           display_name="Claude Opus 4.8", enabled=True,
                           capabilities=["text", "reasoning"], priority=1, temperature=0.2))
    await db_session.commit()

    _Client.payloads = []
    monkeypatch.setattr(inference.httpx, "AsyncClient", _Client)

    r = await inference.complete(db_session, "hi", task="report_drafting", temperature=0.2)
    assert r["ok"] is True, r
    assert r["text"] == "hello"
    # first attempt carried temperature (→400), the retry dropped it (→200)
    assert len(_Client.payloads) == 2
    assert "temperature" in _Client.payloads[0]
    assert "temperature" not in _Client.payloads[1]
