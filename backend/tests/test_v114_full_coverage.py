"""v114 — full-coverage guarantees.

1) Letter attachment sources: PDFs are transcribed CHUNK BY CHUNK (every page
   reaches the model), transient failures retry once, failed chunks surface in
   ``failed_parts`` + an inline Persian marker — never silently dropped.
2) The generation prompt no longer amputates sources at 20k chars: the budgets
   fit whole transcriptions and any cut is explicit (inline marker + warning).
3) The import PDF path retries transient chunk failures, gives failed chunks a
   deferred second pass, and reports honest coverage (chunks_total/failed).
"""
from types import SimpleNamespace

import pytest

from app.ai import inference
from app.services import doc_ingest
from app.services import letter_attachment_extract as lax
from app.services import letter_attachment_generate as gen


async def _resolved_ok(db=None, files=None, model_id=None, task=None, **kw):
    return {"ok": True, "resolved": SimpleNamespace(display_name="TestModel")}


@pytest.fixture
def fast_sleep(monkeypatch):
    """The retry paths sleep 3s between attempts — make that instant in tests."""
    import asyncio
    real = asyncio.sleep

    async def instant(_d, *a, **k):
        await real(0)

    monkeypatch.setattr(asyncio, "sleep", instant)


# ---------------------------------------------------------------------------
# 1) attachment_text — chunked PDF transcription
# ---------------------------------------------------------------------------

async def test_attachment_text_pdf_transcribes_every_chunk(db_session, monkeypatch):
    monkeypatch.setattr(inference, "resolve_multimodal", _resolved_ok)
    monkeypatch.setattr(
        doc_ingest, "pdf_chunks",
        lambda data, max_bytes=0, max_pages=0: iter([(1, b"a"), (9, b"b"), (17, b"c")]))

    async def fake_send(resolved, prompt, files, system=None, max_tokens=8000):
        payload = files[0]["data"]
        return {"ok": True, "text": f"PAGES-{payload.decode()}", "model": "TestModel"}

    monkeypatch.setattr(inference, "send_multimodal", fake_send)
    r = await lax.attachment_text(db_session, data=b"%PDF-fake", filename="big.pdf",
                                  mimetype="application/pdf")
    assert r["ok"] and r["failed_parts"] == [] and not r["truncated"]
    # every chunk transcribed, in page order
    i1, i2, i3 = (r["text"].index(f"PAGES-{c}") for c in ("a", "b", "c"))
    assert i1 < i2 < i3


async def test_attachment_text_pdf_failed_chunk_is_loud_not_silent(db_session, monkeypatch, fast_sleep):
    monkeypatch.setattr(inference, "resolve_multimodal", _resolved_ok)
    monkeypatch.setattr(
        doc_ingest, "pdf_chunks",
        lambda data, max_bytes=0, max_pages=0: iter([(1, b"a"), (9, b"b")]))
    calls = {"b": 0}

    async def fake_send(resolved, prompt, files, system=None, max_tokens=8000):
        if files[0]["data"] == b"b":
            calls["b"] += 1
            return {"ok": False, "error": "timed out (large file?)", "text": ""}
        return {"ok": True, "text": "GOOD-PART"}

    monkeypatch.setattr(inference, "send_multimodal", fake_send)
    r = await lax.attachment_text(db_session, data=b"%PDF-fake", filename="big.pdf",
                                  mimetype="application/pdf")
    assert r["ok"]  # partial success still returns the good pages…
    assert r["failed_parts"] == [9]                    # …but the gap is reported
    assert "GOOD-PART" in r["text"]
    assert "ناموفق" in r["text"] and "صفحهٔ 9" in r["text"]  # inline marker
    assert calls["b"] == 2  # transient error was retried once


async def test_attachment_text_pdf_transient_retry_recovers(db_session, monkeypatch, fast_sleep):
    monkeypatch.setattr(inference, "resolve_multimodal", _resolved_ok)
    monkeypatch.setattr(
        doc_ingest, "pdf_chunks", lambda data, max_bytes=0, max_pages=0: iter([(1, b"a")]))
    state = {"n": 0}

    async def fake_send(resolved, prompt, files, system=None, max_tokens=8000):
        state["n"] += 1
        if state["n"] == 1:
            return {"ok": False, "error": "429: rate limited", "text": ""}
        return {"ok": True, "text": "RECOVERED"}

    monkeypatch.setattr(inference, "send_multimodal", fake_send)
    r = await lax.attachment_text(db_session, data=b"%PDF-fake", filename="p.pdf",
                                  mimetype="application/pdf")
    assert r["ok"] and r["failed_parts"] == [] and "RECOVERED" in r["text"]


async def test_attachment_text_pdf_all_chunks_failed_is_error(db_session, monkeypatch, fast_sleep):
    monkeypatch.setattr(inference, "resolve_multimodal", _resolved_ok)
    monkeypatch.setattr(
        doc_ingest, "pdf_chunks",
        lambda data, max_bytes=0, max_pages=0: iter([(1, b"a"), (9, b"b")]))

    async def fake_send(resolved, prompt, files, system=None, max_tokens=8000):
        return {"ok": False, "error": "500: boom", "text": ""}

    monkeypatch.setattr(inference, "send_multimodal", fake_send)
    r = await lax.attachment_text(db_session, data=b"%PDF-fake", filename="p.pdf",
                                  mimetype="application/pdf")
    assert not r["ok"]


async def test_attachment_text_deterministic_truncated_flag(db_session):
    big = ("سطر آزمایشی\n" * 20000).encode("utf-8")  # far past _TEXT_CAP
    r = await lax.attachment_text(db_session, data=big, filename="t.txt", mimetype="text/plain")
    assert r["ok"] and r["truncated"] and len(r["text"]) == lax._TEXT_CAP


# ---------------------------------------------------------------------------
# 2) generation prompt budgets — no silent 20k amputation
# ---------------------------------------------------------------------------

def test_build_prompt_keeps_whole_source_past_old_20k_cap():
    text = ("د" * 50000) + "END-OF-SOURCE"
    p = gen.build_prompt({}, {}, "بساز", source_files=[{"name": "src.pdf", "text": text}])
    assert "END-OF-SOURCE" in p            # the old [:20000] slice would have cut this
    assert "⚠" not in p                     # nothing was truncated ⇒ no marker


def test_build_prompt_over_cap_cut_is_explicit():
    text = "ه" * (gen.SRC_FILE_CAP + 5000)
    p = gen.build_prompt({}, {}, "بساز", source_files=[{"name": "huge.pdf", "text": text}])
    assert "به سقفِ حجم نرسید" in p          # inline marker for the model
    warns = gen.prompt_size_warnings([{"name": "huge.pdf", "text": text}])
    assert warns and "huge.pdf" in warns[0]


def test_total_budget_spreads_across_files_with_warning():
    files = [{"name": f"f{i}.pdf", "text": "ی" * 100000} for i in range(4)]
    fitted, warns = gen.fit_sources(files)
    assert [len(t) for _, t, _ in fitted[:3]] == [100000, 100000, 100000]
    assert len(fitted[3][1]) == gen.SRC_TOTAL_CAP - 300000  # last file gets the rest
    assert any("f3.pdf" in w for w in warns)
    # build_prompt and the warnings agree (single fit function)
    assert gen.prompt_size_warnings(files) == warns


def test_template_cap_raised_and_cut_warned():
    tt = "ک" * 60000
    p = gen.build_prompt({}, {}, "", template_text=tt, template_name="فرم.xlsx")
    assert p.count("ک") >= 60000            # old cap would have kept only 20k
    big = "گ" * (gen.TEMPLATE_CAP + 10)
    warns = gen.prompt_size_warnings([], big)
    assert warns and "قالب" in warns[0]


# ---------------------------------------------------------------------------
# 3) import PDF path — transient retry + deferred second pass + coverage
# ---------------------------------------------------------------------------

async def test_import_pdf_chunk_retry_and_coverage(db_session, monkeypatch, fast_sleep):
    from app.routers import imports as imp

    monkeypatch.setattr(inference, "resolve_multimodal", _resolved_ok)
    monkeypatch.setattr(
        doc_ingest, "pdf_chunks",
        lambda data, max_bytes=0, max_pages=0: iter([(1, b"good"), (13, b"bad")]))
    calls = {"good": 0, "bad": 0}

    async def fake_send(resolved, prompt, files, system=None, max_tokens=8000):
        tag = files[0]["data"].decode()
        calls[tag] += 1
        if tag == "bad":
            return {"ok": False, "error": "timed out (large file?)", "text": ""}
        return {"ok": True, "text": '{"customers":[{"account_no":"2624-990011-1",'
                                    '"name":"Coverage Co","fields":{"nationality":"UAE"}}]}',
                "model": "TestModel"}

    monkeypatch.setattr(inference, "send_multimodal", fake_send)
    data = b"%PDF-" + b"0" * (imp._PDF_SPLIT_BYTES + 1)  # big enough to chunk
    res = await imp._process_document(db_session, data, "big.pdf", "application/pdf",
                                      None, "tester")
    assert res["ok"]
    assert res["chunks_total"] == 2 and res["chunks_failed"] == 1
    assert res["failed_pages"] == [13]
    assert any("صفحهٔ 13" in e for e in res["chunk_errors"])
    # bad chunk: (send+retry) in the main loop + (send+retry) in the second pass
    assert calls["bad"] == 4 and calls["good"] == 1
    assert any(c.get("account_no") == "990011" for c in res["customers"])


async def test_import_pdf_second_pass_rescues_flaky_chunk(db_session, monkeypatch, fast_sleep):
    from app.routers import imports as imp

    monkeypatch.setattr(inference, "resolve_multimodal", _resolved_ok)
    monkeypatch.setattr(
        doc_ingest, "pdf_chunks",
        lambda data, max_bytes=0, max_pages=0: iter([(1, b"flaky")]))
    state = {"n": 0}

    async def fake_send(resolved, prompt, files, system=None, max_tokens=8000):
        state["n"] += 1
        if state["n"] < 3:  # fails the first send AND its retry…
            return {"ok": False, "error": "connection failed: ConnectError", "text": ""}
        return {"ok": True, "text": '{"customers":[{"account_no":"2624-990022-1",'
                                    '"name":"Rescue Co","fields":{}}]}'}

    monkeypatch.setattr(inference, "send_multimodal", fake_send)
    data = b"%PDF-" + b"0" * (imp._PDF_SPLIT_BYTES + 1)
    res = await imp._process_document(db_session, data, "flaky.pdf", "application/pdf",
                                      None, "tester")
    # …but the deferred second pass rescues it: zero lost chunks
    assert res["ok"] and res["chunks_failed"] == 0 and res["failed_pages"] == []
    assert res["chunk_errors"] == []
    assert any(c.get("account_no") == "990022" for c in res["customers"])
