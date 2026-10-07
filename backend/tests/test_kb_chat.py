"""KB chat (گفت‌وگو با دانش‌نامه): model ranking, KB context, the KB→web flow, the
approve→AI-files-it step, file ingestion, and the data-surface obligations."""
import json

import pytest
from sqlalchemy import select

from app.ai import chat as ai_chat
from app.models.ai_config import AIModel, AIProvider
from app.models.kb import KnowledgeEntry, KnowledgeTopic
from app.models.kb_chat import KbChatFile, KbChatMessage
from app.services import kb_chat, kb_store

USERPW = None


async def _models(db):
    """Three usable models: cheap+fast+web (Gemini flash), pricey Claude, plain OpenAI."""
    db.add_all([
        AIProvider(key="gemini", display_name="Gemini", enabled=True, api_key="g-key"),
        AIProvider(key="anthropic", display_name="Anthropic", enabled=True, api_key="a-key"),
        AIProvider(key="openai", display_name="OpenAI", enabled=True, api_key="o-key"),
        AIProvider(key="off", display_name="Off", enabled=False, api_key="x"),
    ])
    await db.flush()
    db.add_all([
        AIModel(model_key="gemini-2.5-flash", provider_key="gemini", display_name="Gemini 2.5 Flash", enabled=True,
                capabilities=["text", "vision", "fast", "documents", "long_context"], priority=6,
                input_cost_per_1m=0.3, output_cost_per_1m=2.5, context_window=1000000, source="catalog"),
        AIModel(model_key="claude-opus-4-8", provider_key="anthropic", display_name="Claude Opus", enabled=True,
                capabilities=["text", "vision", "reasoning", "documents"], priority=1,
                input_cost_per_1m=15, output_cost_per_1m=75, context_window=200000, source="catalog"),
        AIModel(model_key="gpt-4o", provider_key="openai", display_name="GPT-4o", enabled=True,
                capabilities=["text", "vision"], priority=4, input_cost_per_1m=2.5, context_window=128000, source="catalog"),
        AIModel(model_key="gemini-embedding-001", provider_key="gemini", display_name="Embed", enabled=True,
                capabilities=["text"], priority=1, source="discovered"),
        AIModel(model_key="off-model", provider_key="off", display_name="Off model", enabled=True,
                capabilities=["text", "fast"], priority=1, source="catalog"),
    ])
    await db.commit()


async def test_models_are_ranked_fast_web_cheap_first_and_exclude_unusable(db_session):
    await _models(db_session)
    out = await kb_chat.ranked_models(db_session)
    names = [m["display_name"] for m in out["models"]]
    assert names[0] == "Gemini 2.5 Flash"                       # fast + web + any-file + cheap
    assert "Embed" not in names and "Off model" not in names     # non-chat / provider disabled
    assert out["default_model_id"] == out["models"][0]["id"]
    top = out["models"][0]
    assert top["fast"] and top["web"] and top["files"] and top["cheap"] and top["recommended"]
    opus = next(m for m in out["models"] if m["display_name"] == "Claude Opus")
    assert opus["web"] and not opus["fast"] and not opus["cheap"]
    gpt = next(m for m in out["models"] if m["display_name"] == "GPT-4o")
    assert not gpt["web"]                                       # plain OpenAI has no one-call search


def test_static_kb_export_covers_every_tab():
    data = kb_chat.load_static()
    assert [t["id"] for t in data["tabs"]] == ["saderat", "uae", "intl", "iran", "islamic"]
    assert all(t["sections"] for t in data["tabs"])
    assert all(s["text"].strip() for t in data["tabs"] for s in t["sections"])
    assert data["compare"]


def test_kb_context_whole_when_it_fits_and_ranked_with_index_when_not():
    secs = [{"ref": "تب › ترهین", "text": "ترهین ملک نیازمند ارزیابی است " * 20},
            {"ref": "تب › کارمزد", "text": "کارمزد LG یک درصد است " * 20},
            {"ref": "تب › AECB", "text": "گزارش اعتباری AECB " * 20}]
    whole, m1 = kb_chat.build_kb_context(secs, "کارمزد", 10 ** 6)
    assert not m1["trimmed"] and m1["included_sections"] == 3
    cut, m2 = kb_chat.build_kb_context(secs, "کارمزد LG", 700)
    assert m2["trimmed"] and m2["included_sections"] < 3
    assert "تب › کارمزد" in cut                                  # the relevant one survived
    assert "فهرستِ عنوانِ همهٔ بخش‌ها" in cut and "تب › ترهین" in cut  # nothing hidden from the index


def test_build_request_wires_web_search_and_files_per_family():
    class R:
        def __init__(self, pk, auth="api_key", model="m"):
            self.provider_key, self.auth_scheme, self.api_key = pk, auth, "k"
            self.model_key, self.base_url, self.display_name = model, "", "x"
            self.capabilities, self.max_output_tokens, self.context_window, self.temperature = [], None, None, None
    turns = [{"role": "user", "content": "hi"}]
    f = [{"filename": "a.png", "mimetype": "image/png", "data": b"\x89PNG"}]
    fam, url, hdr, pl = ai_chat.build_request(R("anthropic"), system="S", turns=turns, files=f, web=True, max_tokens=100)
    assert fam == "anthropic" and pl["tools"][0]["type"].startswith("web_search")
    assert pl["messages"][-1]["content"][0]["type"] == "image"
    fam, url, hdr, pl = ai_chat.build_request(R("claude_subscription", "oauth_bearer"), system="S", turns=turns, files=[], web=False, max_tokens=1)
    assert pl["system"][0]["text"].startswith("You are Claude Code") and "tools" not in pl
    fam, url, hdr, pl = ai_chat.build_request(R("gemini", model="gemini-2.5-flash"), system="S", turns=turns, files=f, web=True, max_tokens=1)
    assert pl["tools"] == [{"google_search": {}}] and "inlineData" in pl["contents"][-1]["parts"][0]
    fam, url, hdr, pl = ai_chat.build_request(R("perplexity", model="sonar"), system="S", turns=turns, files=[], web=True, max_tokens=1)
    assert fam == "openai" and "tools" not in pl


def _fake_chat(script):
    """Replace ai_chat.chat; `script` is a list of replies consumed in order. Records calls."""
    calls = []

    async def fake(resolved, *, system, turns, files=None, web=False, max_tokens=8000):
        calls.append({"model": resolved.display_name, "system": system, "turns": turns, "files": files or [], "web": web})
        r = script.pop(0)
        return {"ok": True, "error": None, "model": resolved.display_name, "sources": [], **r} if "error" not in r else \
            {"ok": False, "text": "", "sources": [], "model": resolved.display_name, **r}
    return fake, calls


async def _ask(client, headers, question, **kw):
    data = {"question": question, **{k: str(v) for k, v in kw.items() if k != "files"}}
    files = [("files", f) for f in kw.get("files", [])]
    return await client.post("/api/knowledge/chat/ask", headers=headers, data=data, files=files or None)


async def test_answer_from_kb_is_recorded_in_history_and_the_log(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    await kb_store.upsert_entry(db_session, topic_title="کارمزد LG", content="کارمزد صدور LG برابر ۱٪ است.",
                                category="محاسبات", username="t", tab="uae")
    await db_session.commit()
    fake, calls = _fake_chat([{"text": "کارمزد LG یک درصد است.\nمنبع در دانش‌نامه: بانکداری امارات › محاسبات › کارمزد LG"}])
    monkeypatch.setattr(ai_chat, "chat", fake)

    r = await _ask(client, admin_headers, "کارمزد LG چقدر است؟")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["assistant"]["source"] == "kb" and j["assistant"]["kb_state"] == ""
    # the model saw the WHOLE KB: static sections and the dynamic entry
    prompt = calls[0]["turns"][-1]["content"]
    assert "کارمزد صدور LG برابر ۱٪ است" in prompt and "معرفی و ساختار دایره تسهیلات اعطایی" in prompt
    assert calls[0]["web"] is False
    # default model = the top-ranked one
    assert calls[0]["model"] == "Gemini 2.5 Flash"

    hist = (await client.get(f"/api/knowledge/chat/sessions/{j['session_id']}", headers=admin_headers)).json()
    assert [m["role"] for m in hist["messages"]] == ["user", "assistant"]
    lst = (await client.get("/api/knowledge/chat/sessions", headers=admin_headers)).json()["sessions"]
    assert lst[0]["id"] == j["session_id"] and "کارمزد LG" in lst[0]["title"]
    logs = (await client.get("/api/audit/?entity_type=kb_chat", headers=admin_headers)).json()
    assert logs["total"] == 1 and "کارمزد LG چقدر است" in logs["items"][0]["detail"]


async def test_not_in_kb_goes_to_web_then_approve_files_it_under_the_right_tab(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    fake, calls = _fake_chat([
        {"text": f"{kb_chat.NOT_IN_KB}\nدرباره سقف وثیقه در دانش‌نامه چیزی نبود."},
        {"text": "بر اساس بخشنامه ۱۴۰۴ بانک مرکزی، سقف ۷۰٪ ارزش وثیقه است.",
         "sources": [{"url": "https://cbi.ir/x", "title": "CBI"}]},
    ])
    monkeypatch.setattr(ai_chat, "chat", fake)
    r = await _ask(client, admin_headers, "سقف ارزش وثیقه در ایران چند درصد است؟")
    a = r.json()["assistant"]
    assert a["source"] == "web" and a["kb_state"] == "pending" and a["sources"][0]["url"] == "https://cbi.ir/x"
    assert [c["web"] for c in calls] == [False, True]            # KB first, then the web
    assert (await db_session.execute(select(KnowledgeEntry))).scalars().first() is None   # nothing filed yet

    from app.ai import inference

    async def fake_complete(db, prompt, **kw):
        assert "ساختارِ فعلیِ دانش‌نامه" in prompt and "بخشنامه ۱۴۰۴" in prompt
        return {"ok": True, "model": "m", "error": None, "text": "```json\n" + json.dumps({
            "tab": "iran", "category": "وثایق", "topic_title": "سقف ارزش وثیقه",
            "content": "بر اساس بخشنامه ۱۴۰۴ بانک مرکزی، سقف تسهیلات ۷۰٪ ارزش وثیقه است."}, ensure_ascii=False) + "\n```"}
    monkeypatch.setattr(inference, "complete", fake_complete)

    ap = await client.post(f"/api/knowledge/chat/messages/{a['id']}/approve", headers=admin_headers, json={})
    assert ap.status_code == 200, ap.text
    body = ap.json()
    assert body["placement"] == "بانکداری ایران › وثایق › سقف ارزش وثیقه" and body["tab"] == "iran"
    topic = (await db_session.execute(select(KnowledgeTopic))).scalars().one()
    entry = (await db_session.execute(select(KnowledgeEntry))).scalars().one()
    assert topic.tab == "iran" and entry.source_kind == "chat_web" and "https://cbi.ir/x" in entry.content
    assert "گفت‌وگوی دانش‌نامه" in entry.source_ref

    # the page's list shows it under the iran tab; a second click is a no-op
    kb = (await client.get("/api/knowledge/", headers=admin_headers)).json()
    assert kb["topics"][0]["tab"] == "iran"
    again = await client.post(f"/api/knowledge/chat/messages/{a['id']}/approve", headers=admin_headers, json={})
    assert again.json()["already"] is True
    assert len((await db_session.execute(select(KnowledgeEntry))).scalars().all()) == 1
    # …and the filing is in the activity log
    logs = (await client.get("/api/audit/?entity_type=knowledge", headers=admin_headers)).json()
    assert logs["total"] == 1


async def test_approve_never_guesses_the_tab(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    fake, _ = _fake_chat([{"text": f"{kb_chat.NOT_IN_KB}\nنبود"}, {"text": "پاسخ وب"}])
    monkeypatch.setattr(ai_chat, "chat", fake)
    a = (await _ask(client, admin_headers, "سؤالِ دور از همه چیز؟")).json()["assistant"]
    from app.ai import inference

    async def fake_complete(db, prompt, **kw):
        return {"ok": True, "model": "m", "error": None, "text": json.dumps(
            {"tab": "???", "category": "c", "topic_title": "t", "content": "پاسخ وب"}, ensure_ascii=False)}
    monkeypatch.setattr(inference, "complete", fake_complete)
    r = await client.post(f"/api/knowledge/chat/messages/{a['id']}/approve", headers=admin_headers, json={})
    assert r.status_code == 409 and r.json()["error"] == "tab_unclear"
    ok = await client.post(f"/api/knowledge/chat/messages/{a['id']}/approve", headers=admin_headers, json={"tab": "uae"})
    assert ok.status_code == 200 and ok.json()["tab"] == "uae"


async def test_a_lossy_rewrite_never_replaces_the_answer(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    long_answer = "نرخ سود ۲۳ درصد و کارمزد ۱ درصد و سقف ۷۰ درصد و مدت ۶۰ ماه است. " * 6
    fake, _ = _fake_chat([{"text": f"{kb_chat.NOT_IN_KB}\nنبود"}, {"text": long_answer}])
    monkeypatch.setattr(ai_chat, "chat", fake)
    a = (await _ask(client, admin_headers, "شرایط تسهیلات؟")).json()["assistant"]
    from app.ai import inference

    async def fake_complete(db, prompt, **kw):
        return {"ok": True, "model": "m", "error": None, "text": json.dumps(
            {"tab": "iran", "category": "c", "topic_title": "شرایط", "content": "تسهیلات شرایط دارد."}, ensure_ascii=False)}
    monkeypatch.setattr(inference, "complete", fake_complete)
    r = await client.post(f"/api/knowledge/chat/messages/{a['id']}/approve", headers=admin_headers, json={})
    assert r.status_code == 200
    entry = (await db_session.execute(select(KnowledgeEntry))).scalars().one()
    assert "۲۳ درصد" in entry.content and "۷۰ درصد" in entry.content


async def test_web_off_and_no_web_model_are_said_not_hidden(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    fake, calls = _fake_chat([{"text": f"{kb_chat.NOT_IN_KB}\nنبود"}])
    monkeypatch.setattr(ai_chat, "chat", fake)
    r = await _ask(client, admin_headers, "پرسش بی‌پاسخ؟", allow_web="false")
    a = r.json()["assistant"]
    assert a["source"] == "none" and "جستجوی وب خاموش بود" in a["content"] and len(calls) == 1


async def test_files_are_read_in_full_stored_verbatim_and_sent_to_the_model(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    body = "\n".join(f"ردیف {i}: مبلغ {i * 1000} درهم" for i in range(1, 400))
    fake, calls = _fake_chat([{"text": "ردیف ۳۹۹ مبلغ ۳۹۹۰۰۰ است."}])
    monkeypatch.setattr(ai_chat, "chat", fake)
    r = await _ask(client, admin_headers, "ردیف ۳۹۹ چقدر است؟",
                   files=[("statement.txt", body.encode("utf-8"), "text/plain"),
                          ("note.csv", "a,b\n1,2\n".encode(), "text/csv")])
    assert r.status_code == 200, r.text
    prompt = calls[0]["turns"][-1]["content"]
    assert "ردیف 399: مبلغ 399000 درهم" in prompt and "ردیف 1: مبلغ 1000 درهم" in prompt   # first AND last line: no summarising
    rows = (await db_session.execute(select(KbChatFile).order_by(KbChatFile.filename))).scalars().all()
    assert [f.filename for f in rows] == ["note.csv", "statement.txt"]
    st = next(f for f in rows if f.filename == "statement.txt")
    assert st.text == body and st.text_chars == len(body) and st.extract_status == "ok"
    assert st.store in ("local", "drive") and st.message_id               # kept, linked to the question
    hist = (await client.get(f"/api/knowledge/chat/sessions/{r.json()['session_id']}", headers=admin_headers)).json()
    assert {f["filename"] for f in hist["files"]} == {"note.csv", "statement.txt"}
    if st.store == "local":                                                 # the honest fallback says so
        assert "Drive" in (st.store_note or "") or "درایو" in (st.store_note or "")
    raw = await client.get(f"/api/knowledge/chat/files/{st.id}/raw", headers=admin_headers)
    assert raw.status_code == 200 and raw.content.decode("utf-8") == body


async def test_a_file_too_big_for_the_model_stops_instead_of_being_cut(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    m = (await db_session.execute(select(AIModel).where(AIModel.model_key == "gpt-4o"))).scalar_one()
    mid = m.id
    m.context_window = 10000                                                # ≈ 16k characters
    await db_session.commit()
    fake, calls = _fake_chat([])
    monkeypatch.setattr(ai_chat, "chat", fake)
    r = await _ask(client, admin_headers, "چه نوشته؟", model_id=mid,
                   files=[("big.txt", ("ب" * 60000).encode("utf-8"), "text/plain")])
    a = r.json()["assistant"]
    assert calls == [] and a["source"] == "none" and "بیشتر است" in a["content"] and "بریده نشود" in a["content"]


async def test_unreadable_file_is_named_not_skipped(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    fake, calls = _fake_chat([{"text": "ok"}])
    monkeypatch.setattr(ai_chat, "chat", fake)
    await _ask(client, admin_headers, "این چیه؟", files=[("legacy.doc", b"\xd0\xcf\x11\xe0 binary", "application/msword")])
    assert "legacy.doc" in calls[0]["turns"][-1]["content"] and "خوانده‌نشده" in calls[0]["turns"][-1]["content"]


async def test_a_scanned_or_image_file_travels_natively_to_a_vision_model(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    fake, calls = _fake_chat([{"text": "تصویر را دیدم"}])
    monkeypatch.setattr(ai_chat, "chat", fake)
    await _ask(client, admin_headers, "تصویر چیست؟", files=[("scan.png", b"\x89PNG\r\n\x1a\n" + b"0" * 50, "image/png")])
    assert calls[0]["files"] and calls[0]["files"][0]["mimetype"] == "image/png"


async def test_oversize_file_is_refused_up_front(client, admin_headers, db_session, monkeypatch):
    await _models(db_session)
    monkeypatch.setattr(kb_chat, "MAX_FILE_MB", 1)
    r = await _ask(client, admin_headers, "سؤال؟", files=[("x.txt", b"a" * (1024 * 1024 + 10), "text/plain")])
    assert r.status_code == 413


async def test_no_model_configured_says_so(client, admin_headers, db_session):
    r = await _ask(client, admin_headers, "سؤال؟")
    assert r.status_code == 200 and r.json()["assistant"]["source"] == "none"
    assert "تنظیم نشده" in r.json()["assistant"]["content"]


async def test_sessions_are_private_to_their_owner(client, admin_headers, auth_headers, db_session, monkeypatch):
    await _models(db_session)
    fake, _ = _fake_chat([{"text": "پاسخ"}])
    monkeypatch.setattr(ai_chat, "chat", fake)
    sid = (await _ask(client, admin_headers, "سؤال خصوصی؟")).json()["session_id"]
    other = await client.get(f"/api/knowledge/chat/sessions/{sid}", headers=auth_headers)
    assert other.status_code == 404
    assert (await client.get("/api/knowledge/chat/sessions", headers=auth_headers)).json()["sessions"] == []


async def test_models_endpoint_reports_limits_and_sync_status(client, admin_headers, db_session):
    await _models(db_session)
    j = (await client.get("/api/knowledge/chat/models", headers=admin_headers)).json()
    assert j["models"][0]["display_name"] == "Gemini 2.5 Flash"
    assert j["limits"]["max_file_mb"] >= 1 and "interval_hours" in j["sync"]


async def test_chat_tables_are_in_the_backup():
    from app.services.backup import _targets
    names = {m.__tablename__ for m in _targets().values()}
    assert {"kb_chat_sessions", "kb_chat_messages", "kb_chat_files"} <= names


async def test_same_title_under_two_tabs_stays_two_topics(db_session):
    a = await kb_store.upsert_entry(db_session, topic_title="ضمانت‌نامه", content="الف", tab="uae")
    b = await kb_store.upsert_entry(db_session, topic_title="ضمانت‌نامه", content="ب", tab="iran")
    assert a["topic_id"] != b["topic_id"]
    legacy = await kb_store.upsert_entry(db_session, topic_title="ضمانت‌نامه", content="ج")   # no tab = old behaviour
    assert legacy["topic_id"] in (a["topic_id"], b["topic_id"])
