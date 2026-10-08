"""«هر نوع فرمتی باید خونده بشه … کامل، نه خلاصه» — every format, the WHOLE text.

Exercises inspection_formats / inspection_media through this project's own
extractor (`_extract`), on genuine files where they exist: a real Word-97 .doc
and Outlook .msg (Apache POI's public test data), a real Excel-97 .xls (xlwt).
"""
import io
import json
import urllib.error
import zipfile
from email.message import EmailMessage
from pathlib import Path

import pytest

from app.services import inspection_media as _media
from app.services.inspection_files import extract as _extract

FIX = Path(__file__).parent / "fixtures" / "inspection_formats"


def _zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_word_97_doc_in_full():
    ex = _extract((FIX / "SampleDoc.doc").read_bytes(), "x.doc", "")
    assert ex["status"] == "ok"
    assert "I am a test document" in ex["text"] and "It’s also in blue" in ex["text"], "first AND last line"


def test_outlook_msg():
    ex = _extract((FIX / "quick.msg").read_bytes(), "mail.msg", "")
    assert ex["status"] == "ok" and "Test the content transformer" in ex["text"]
    assert "The quick brown fox jumps over the lazy dog" in ex["text"]


def test_excel_97_xls_every_sheet():
    xlwt = pytest.importorskip("xlwt")
    wb = xlwt.Workbook()
    a, b = wb.add_sheet("هزینه"), wb.add_sheet("درآمد")
    a.write(0, 0, "نام"); a.write(1, 0, "علی"); a.write(1, 1, 1200)
    b.write(0, 0, "پایانِ کاربرگِ دوم")
    buf = io.BytesIO(); wb.save(buf)
    ex = _extract(buf.getvalue(), "book.xls", "")
    assert ex["status"] == "ok" and "علی" in ex["text"] and "1200" in ex["text"] and "پایانِ کاربرگِ دوم" in ex["text"]


def test_rtf_with_unicode_escapes():
    word = "".join("\\u%d?" % ord(c) for c in "سلام")
    rtf = ("{\\rtf1\\ansi\\uc1 " + word + " world\\par second line}").encode()
    ex = _extract(rtf, "note.rtf", "")
    assert ex["status"] == "ok" and "سلام world" in ex["text"] and "second line" in ex["text"]


def test_opendocument_and_epub():
    content = ('<office:document-content xmlns:office="o" xmlns:text="t"><office:body><office:text>'
               '<text:p>بندِ اول</text:p><text:p>بندِ آخر</text:p></office:text></office:body></office:document-content>')
    ex = _extract(_zip({"mimetype": "application/vnd.oasis.opendocument.text", "content.xml": content}), "a.odt", "")
    assert ex["status"] == "ok" and "بندِ اول" in ex["text"] and "بندِ آخر" in ex["text"]
    opf = ('<package><manifest><item id="c2" href="two.xhtml"/><item id="c1" href="one.xhtml"/></manifest>'
           '<spine><itemref idref="c1"/><itemref idref="c2"/></spine></package>')
    book = _zip({"META-INF/container.xml": '<container><rootfile full-path="OEBPS/b.opf"/></container>',
                 "OEBPS/b.opf": opf, "OEBPS/one.xhtml": "<p>فصل یک</p>", "OEBPS/two.xhtml": "<p>فصل دو</p>"})
    ex = _extract(book, "book.epub", "")
    assert ex["status"] == "ok" and ex["text"].index("فصل یک") < ex["text"].index("فصل دو")


def test_email_with_its_attachments():
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = "a@x.com", "b@x.com", "قرارداد"
    m.set_content("متنِ ایمیل")
    m.add_attachment("محتوای پیوست".encode(), maintype="text", subtype="plain", filename="p.txt")
    ex = _extract(m.as_bytes(), "m.eml", "")
    assert ex["status"] == "ok" and "متنِ ایمیل" in ex["text"] and "محتوای پیوست" in ex["text"]


def test_zip_reads_every_member_recursively():
    inner = _zip({"deep/notes.md": "# عمیق\nخطِ آخرِ درونی"})
    doc = (FIX / "SampleDoc.doc").read_bytes()
    ex = _extract(_zip({"a.txt": "سلام", "b/c.doc": doc, "inner.zip": inner}), "bundle.zip", "")
    assert ex["status"] == "ok"
    for needle in ("سلام", "I am a test document", "خطِ آخرِ درونی"):
        assert needle in ex["text"], needle


def test_any_text_whatever_its_extension():
    ex = _extract("key = مقدار\nline 2".encode(), "settings.conf9", "")
    assert ex["status"] == "ok" and "مقدار" in ex["text"]


def test_media_waits_for_a_full_transcript_and_zip_with_media_too():
    assert _extract(b"ID3....", "voice.mp3", "audio/mpeg")["status"] == "pending"
    ex = _extract(_zip({"a.txt": "x", "talk.ogg": b"OggS"}), "z.zip", "")
    assert ex["status"] == "pending" and "x" in ex["text"]


def test_transcription_continues_to_the_end_via_files_api(monkeypatch):
    calls = {"gen": 0, "upload": 0, "deleted": 0}

    class Resp:
        def __init__(self, body=b"{}", headers=None):
            self._b, self.headers = body, headers or {}

        def read(self):
            return self._b

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake(req, timeout=None):
        url, method = req.full_url, req.get_method()
        if "/models?" in url:
            return Resp(json.dumps({"models": []}).encode())
        if "/upload/v1beta/files" in url:
            calls["upload"] += 1
            return Resp(headers={"x-goog-upload-url": "https://up.example/s"})
        if url.startswith("https://up.example/s"):
            return Resp(json.dumps({"file": {"name": "files/a", "uri": "gs://a", "state": "ACTIVE"}}).encode())
        if method == "DELETE":
            calls["deleted"] += 1
            return Resp()
        calls["gen"] += 1
        assert b"gs://a" in req.data
        text = "[00:00:00] بخشِ اول " if calls["gen"] == 1 else "[00:10:00] بخشِ آخر\n<<END>>"
        return Resp(json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode())

    monkeypatch.setattr(_media.urllib.request, "urlopen", fake)
    monkeypatch.setattr(_media, "INLINE_MAX", 10)
    res = _media.transcribe(b"0" * 100, "talk.mp3", "audio/mpeg", api_key="k")
    assert res["ok"] and not res["truncated"]
    assert "بخشِ اول" in res["text"] and "بخشِ آخر" in res["text"] and "<<END>>" not in res["text"]
    assert calls == {"gen": 2, "upload": 1, "deleted": 1}


def test_no_key_is_said_plainly(monkeypatch):
    for k in ("INSPECTION_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_AI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(_media, "KEY_PROVIDERS", [])
    res = _media.finish_extraction({"status": "pending", "text": "", "note": ""}, b"x", "a.mp3", "audio/mpeg")
    assert res["status"] == "failed" and "GEMINI_API_KEY" in res["note"]
