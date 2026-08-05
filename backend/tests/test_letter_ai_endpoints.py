"""The /api/letter-ai endpoints: model listing + analyze.

``analyze`` is exercised with the provider call MOCKED (no network / no key) so we
test our own wiring — DB-fact gathering, prompt hand-off, and the validation gate
that filters the model's proposals — deterministically.
"""
import json

import pytest

from app.models.customer import Customer
from app.models.facility import Facility
from app.models.ai_config import AIProvider, AIModel


async def _seed_usable_model(db_session):
    """A provider with a key + one enabled model → resolvable/usable."""
    db_session.add(AIProvider(key="anthropic", display_name="Anthropic",
                              enabled=True, auth_scheme="api_key",
                              base_url="https://api.anthropic.com", api_key="sk-test-xxx"))
    db_session.add(AIModel(model_key="claude-opus-4-8", provider_key="anthropic",
                           display_name="Claude Opus 4.8", enabled=True,
                           capabilities=["text", "reasoning"], priority=1))
    await db_session.commit()


async def test_models_endpoint_lists_usable(client, auth_headers, db_session):
    await _seed_usable_model(db_session)
    r = await client.get("/api/letter-ai/models", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["available"] is True
    assert any(m["display_name"] == "Claude Opus 4.8" for m in body["models"])
    # tools catalog travels with it so UI/back never drift
    tool_ids = {t["id"] for t in body["tools"]}
    assert {"spelling", "consistency", "validation"} <= tool_ids


async def test_models_endpoint_empty_when_nothing_configured(client, auth_headers):
    r = await client.get("/api/letter-ai/models", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["available"] is False


async def test_analyze_validates_model_output(client, auth_headers, db_session, monkeypatch):
    await _seed_usable_model(db_session)
    db_session.add(Customer(account_no="770100", name="Sample Co", account_type="corporate", branch="2624"))
    await db_session.commit()
    db_session.add(Facility(id="F-770100-1", customer_id=(
        await _customer_id(db_session, "770100")), facility_type="overdraft",
        amount=100000, currency="AED", interest_rate=12, status="active"))
    await db_session.commit()

    # The model "returns" three proposals; only the valid ones must survive.
    async def fake_complete(db, prompt, **kwargs):
        # The prompt must carry the DB facts + the body text (so the model could
        # validate against them) — assert the wiring really passed them through.
        assert "حقایقِ پایگاه‌داده" in prompt
        assert "اعطا گردید" in prompt
        # the gathered selections must reach the prompt as numbered targets
        assert "موارد انتخاب‌شده" in prompt
        assert "مبلغ ۵۰۰۰۰ درهم" in prompt
        return {"ok": True, "model": "Claude Opus 4.8", "error": None, "text": json.dumps({
            "changes": [
                {"op": "text_replace", "field": "body", "category": "spelling",
                 "title": "اصلاح فعل", "find": "اعطا گردید", "replace": "اعطا شد", "severity": "low"},
                {"op": "text_replace", "field": "body", "category": "spelling",
                 "title": "توهم", "find": "عبارتی که وجود ندارد", "replace": "x"},
                {"op": "note", "field": "body", "category": "consistency",
                 "title": "مبلغ با پایگاه‌داده هم‌خوان است", "severity": "low"},
            ]
        }, ensure_ascii=False)}

    import app.routers.letter_ai as mod
    monkeypatch.setattr(mod.inference, "complete", fake_complete)

    r = await client.post("/api/letter-ai/analyze", headers=auth_headers, json={
        "account_no": "770100",
        "fields": {"body": "<div>مبلغ ۵۰۰۰۰ درهم بابت تسهیلات اعطا گردید.</div>",
                   "subject": "موضوع"},
        "tools": ["spelling", "consistency", "validation"],
        "selections": ["مبلغ ۵۰۰۰۰ درهم"],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["facts_used"] is True
    # 3 proposed → 2 survive (the hallucinated text_replace is dropped)
    titles = [c["title"] for c in body["changes"]]
    assert "اصلاح فعل" in titles
    assert "مبلغ با پایگاه‌داده هم‌خوان است" in titles
    assert "توهم" not in titles


async def test_analyze_stages_db_writes(client, auth_headers, db_session, monkeypatch):
    await _seed_usable_model(db_session)
    db_session.add(Customer(account_no="780100", name="Primary LLC", account_type="corporate"))
    await db_session.commit()

    async def fake_complete(db, prompt, **kwargs):
        # the db_extract guide must be in the prompt when the tool is on
        assert "db_write" in prompt
        return {"ok": True, "model": "m", "error": None, "text": json.dumps({"changes": [
            {"op": "db_write", "account_no": "780100", "customer_name": "Primary LLC",
             "key": "email", "value": "info@primary.co"},
            {"op": "db_write", "account_no": "", "customer_name": "Unknown Person",
             "key": "phone", "value": "050"},  # unresolved → note, not guessed
        ]}, ensure_ascii=False)}

    import app.routers.letter_ai as mod
    monkeypatch.setattr(mod.inference, "complete", fake_complete)

    r = await client.post("/api/letter-ai/analyze", headers=auth_headers, json={
        "account_no": "780100", "fields": {"body": "<div>x</div>"},
        "tools": ["db_extract"],
    })
    assert r.status_code == 200, r.text
    changes = r.json()["changes"]
    dbw = [c for c in changes if c["op"] == "db_write"]
    notes = [c for c in changes if c["op"] == "note"]
    assert any(c["key"] == "email" and c["account_no"] == "780100" and c["action"] == "add" for c in dbw)
    assert any("شناسایی نشد" in c["title"] for c in notes)  # unknown customer surfaced


async def test_analyze_inline_prompts_rewrites_and_stages_db_write(
    client, auth_headers, db_session, monkeypatch,
):
    """Owner scenario end-to-end: an in-text INSTRUCTION («... این موارد ثبت بشه»)
    plus a lone «؟» placeholder. With the inline_prompts + complete tools on
    (and WITHOUT db_extract), the analyze wiring must: carry both tool guides,
    keep the instruction-replacement + completion changes, and stage the
    db_write the instruction asked for."""
    await _seed_usable_model(db_session)
    db_session.add(Customer(account_no="790100", name="Alpha LLC", account_type="corporate"))
    await db_session.commit()

    body_html = ("<div>احتراماً به استحضار می‌رساند حساب جاری مشتری فعال است ؟</div>"
                 "<div>اینجا یه جمله بنویس که ایمیل جدید مشتری info@alpha.co اعلام و ثبت بشه</div>")

    async def fake_complete(db, prompt, **kwargs):
        # both new tool guides must reach the model
        assert "علامتِ سؤال" in prompt          # complete tool guide
        assert "دستور یا خواستهٔ نویسنده" in prompt  # inline_prompts guide
        return {"ok": True, "model": "m", "error": None, "text": json.dumps({"changes": [
            {"op": "text_replace", "field": "body", "category": "complete",
             "title": "تکمیل جملهٔ ناتمام",
             "find": "حساب جاری مشتری فعال است ؟",
             "replace": "حساب جاری مشتری فعال بوده و گردش آن مطلوب ارزیابی می‌گردد.",
             "severity": "medium"},
            {"op": "text_replace", "field": "body", "category": "inline_prompts",
             "title": "اجرای دستور داخل متن",
             "find": "اینجا یه جمله بنویس که ایمیل جدید مشتری info@alpha.co اعلام و ثبت بشه",
             "replace": "بدین‌وسیله نشانی پست الکترونیکی جدید مشتری info@alpha.co اعلام می‌گردد.",
             "severity": "medium"},
            {"op": "db_write", "account_no": "790100", "customer_name": "Alpha LLC",
             "key": "email", "value": "info@alpha.co"},
        ]}, ensure_ascii=False)}

    import app.routers.letter_ai as mod
    monkeypatch.setattr(mod.inference, "complete", fake_complete)

    r = await client.post("/api/letter-ai/analyze", headers=auth_headers, json={
        "account_no": "790100", "fields": {"body": body_html},
        "tools": ["complete", "inline_prompts"],   # db_extract NOT ticked
    })
    assert r.status_code == 200, r.text
    changes = r.json()["changes"]
    cats = {c["category"] for c in changes}
    assert "complete" in cats and "inline_prompts" in cats
    # the completion + instruction-replacement survive the find-guard
    replaces = [c for c in changes if c["op"] == "text_replace"]
    assert len(replaces) == 2 and all(c["applicable"] for c in replaces)
    # and the requested DB record is STAGED even without db_extract ticked
    dbw = [c for c in changes if c["op"] == "db_write"]
    assert any(c["key"] == "email" and c["account_no"] == "790100" for c in dbw)


async def test_analyze_no_model_is_friendly(client, auth_headers, db_session, monkeypatch):
    # No model configured → inference returns no_model; endpoint stays 200 + ok:false.
    async def fake_complete(db, prompt, **kwargs):
        return {"ok": False, "error": "no_model", "text": "", "model": None}

    import app.routers.letter_ai as mod
    monkeypatch.setattr(mod.inference, "complete", fake_complete)

    r = await client.post("/api/letter-ai/analyze", headers=auth_headers, json={
        "fields": {"body": "<div>متن</div>"}, "tools": ["spelling"],
    })
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert r.json()["error"] == "no_model"
    assert r.json()["changes"] == []


async def _customer_id(db_session, acc):
    from sqlalchemy import select
    c = (await db_session.execute(select(Customer).where(Customer.account_no == acc))).scalar_one()
    return c.id


async def test_analyze_need_logs_second_round(client, auth_headers, db_session, monkeypatch):
    """v67: when the model asks need_logs, the server searches the WHOLE logs
    and re-runs once with the results; the final changes payload wins."""
    from datetime import datetime
    from app.models.audit_log import AuditLog

    await _seed_usable_model(db_session)
    db_session.add(Customer(account_no="770100", name="Sample Co",
                            account_type="corporate", branch="2624"))
    db_session.add(AuditLog(id="old1", username="mahdi", action="print",
                            entity_type="letter", account_no="770100",
                            detail="چاپ نامهٔ ترهین قدیمی",
                            created_at=datetime(2025, 1, 5, 10, 0, 0)))
    await db_session.commit()

    calls = []

    async def fake_complete(db, prompt, **kwargs):
        calls.append(prompt)
        if len(calls) == 1:
            # facts advertise the protocol; the model uses it
            assert "need_logs" in prompt
            return {"ok": True, "model": "m", "error": None,
                    "text": json.dumps({"need_logs": {"scope": "audit", "text": "ترهین"}},
                                       ensure_ascii=False)}
        # round 2: the search results (incl. the OLD row) must be in the prompt
        assert "نتایجِ جستجوی لاگ‌ها" in prompt
        assert "چاپ نامهٔ ترهین قدیمی" in prompt
        assert "audit_total" in prompt
        return {"ok": True, "model": "m", "error": None, "text": json.dumps({
            "changes": [{"op": "note", "field": "body", "category": "consistency",
                         "title": "لاگِ چاپِ قبلی یافت شد", "severity": "low"}]
        }, ensure_ascii=False)}

    import app.routers.letter_ai as mod
    monkeypatch.setattr(mod.inference, "complete", fake_complete)

    r = await client.post("/api/letter-ai/analyze", headers=auth_headers, json={
        "account_no": "770100",
        "fields": {"body": "<div>متن</div>", "subject": "موضوع"},
        "tools": ["validation"],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True and len(calls) == 2
    assert [c["title"] for c in body["changes"]] == ["لاگِ چاپِ قبلی یافت شد"]


async def test_analyze_feeds_archive_style_samples(client, auth_headers, db_session, monkeypatch):
    """v88 — saved letters (long bodies, not the letter being edited) reach the
    prompt as tone exemplars; short letters and the current letter are skipped."""
    import json as _json

    from app.models.letter import Letter
    from app.routers import letter_ai as mod

    cur_body = "<div>" + ("متن نامهٔ در حالِ ویرایش است. " * 12) + "</div>"
    db_session.add(Letter(id="LSTY1", account_no="", category="general", title="t1",
                          subject="", recipient_dept="", recipient_manager="",
                          values_json=_json.dumps({
                              "subject": "پیگیری بیمه‌نامه",
                              "body": "<div>" + ("احتراماً به استحضار می‌رساند مراتب جهت اقدام ایفاد می‌گردد. " * 8) + "</div>"},
                              ensure_ascii=False)))
    db_session.add(Letter(id="LSTY2", account_no="", category="general", title="t2",
                          subject="", recipient_dept="", recipient_manager="",
                          values_json=_json.dumps({"subject": "کوتاه", "body": "<div>خیلی کوتاه</div>"},
                                                  ensure_ascii=False)))
    db_session.add(Letter(id="LSTY3", account_no="", category="general", title="t3",
                          subject="", recipient_dept="", recipient_manager="",
                          values_json=_json.dumps({"subject": "خودِ نامه", "body": cur_body},
                                                  ensure_ascii=False)))
    await db_session.commit()

    seen = {}

    async def fake_complete(db, prompt, **kwargs):
        seen["prompt"] = prompt
        return {"ok": True, "model": "fake", "text": '{"changes": []}'}

    monkeypatch.setattr(mod.inference, "complete", fake_complete)
    r = await client.post("/api/letter-ai/analyze",
                          json={"fields": {"body": cur_body}, "tools": ["paragraphs"]},
                          headers=auth_headers)
    assert r.status_code == 200, r.text
    p = seen["prompt"]
    assert "نمونه‌نامه‌های آرشیو" in p
    assert "به استحضار می‌رساند مراتب جهت اقدام" in p      # long archive letter included
    assert "خیلی کوتاه" not in p                            # too short → skipped
    assert p.count("متن نامهٔ در حالِ ویرایش است") <= 13    # current letter NOT re-fed as a sample


async def test_generate_attachment_uses_long_deadline_and_retries(
    client, auth_headers, db_session, monkeypatch
):
    """v89 — the generator passes an explicit long timeout (the 60s default
    expired with several source files) and retries ONCE on a transient error."""
    from app.routers import letter_ai as mod

    calls = []

    async def fake_complete(db, prompt, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {"ok": False, "error": "request timed out", "model": "m"}
        return {"ok": True, "model": "m", "text":
                '{"kind": "excel", "filename": "گزارش تست", "title": "t",'
                ' "sheets": [{"name": "s", "columns": ["c"], "rows": [["1"]]}]}'}

    monkeypatch.setattr(mod.inference, "complete", fake_complete)
    r = await client.post("/api/letter-ai/generate-attachment", headers=auth_headers, json={
        "letter_id": "L-TMO", "account_no": "", "instruction": "جدول تستی بساز",
        "source_files": [{"name": "a.xlsx", "text": "ستون,مقدار\nالف,1"}],
    })
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True
    assert len(calls) == 2                       # timed out once → retried once
    assert all(k.get("timeout") == 240.0 for k in calls)


async def test_analyze_uses_long_deadline_and_retries(client, auth_headers, db_session, monkeypatch):
    """v93 — analyze passes an explicit long timeout and retries once on a
    transient failure (same treatment the generator got in v89)."""
    from app.routers import letter_ai as mod

    calls = []

    async def fake_complete(db, prompt, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {"ok": False, "error": "request timed out", "model": "m"}
        return {"ok": True, "model": "m", "text": '{"changes": []}'}

    monkeypatch.setattr(mod.inference, "complete", fake_complete)
    r = await client.post("/api/letter-ai/analyze", headers=auth_headers, json={
        "fields": {"body": "<div>متن آزمایشی نامه</div>"}, "tools": ["paragraphs"],
    })
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True
    assert len(calls) == 2                       # timed out once → retried once
    assert all(k.get("timeout") == 240.0 for k in calls)
