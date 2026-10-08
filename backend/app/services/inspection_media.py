"""«نظارت و سرکشی» — audio and video read IN FULL, as text.

The owner (2026-10-08, for all of their projects): «صدا و ویدیو هم باید بشه … و
حتی کامل هم خونده بشه نه خلاصه و یا اوایل اون فایل». The supervisor cannot
hear, so the server turns the media into a COMPLETE verbatim transcript with
timestamps (video: plus a description of every scene and any text on screen),
and the read-debt rule then makes the supervisor read all of it.

How it stays complete:
  * the model is told to transcribe verbatim — no summary, nothing skipped — and
    to finish with an explicit «<<END>>» line;
  * an answer that stops before the marker (output-token ceiling) is CONTINUED on
    the same file «from exactly where you stopped», up to MAX_ROUNDS; reaching the
    cap is reported as `truncated`, never hidden;
  * above INLINE_MAX the file goes through Gemini's Files API (resumable), so the
    100 MB attachment ceiling applies, not a 20 MB request limit.

Synchronous and standard-library only (urllib) so it fits every project; an
async caller wraps it in `asyncio.to_thread`. The key: the project's own key
store first (append a callable to KEY_PROVIDERS), then the usual env vars.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

logger = logging.getLogger("inspection.media")

API = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com").rstrip("/")
INLINE_MAX = 15 * 1024 * 1024
MAX_ROUNDS = 40
END = "<<END>>"
TIMEOUT = float(os.getenv("INSPECTION_TRANSCRIBE_TIMEOUT", "900"))

_MEDIA_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".oga", ".opus", ".flac", ".aac", ".amr", ".wma", ".aif",
              ".aiff", ".weba", ".mp4", ".mov", ".mkv", ".webm", ".avi", ".3gp", ".m4v", ".wmv", ".mpeg",
              ".mpg", ".mts")

#: project-specific key sources, tried before the environment
KEY_PROVIDERS: list[Callable[[], Optional[str]]] = []
_ENV_KEYS = ("INSPECTION_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_AI_API_KEY", "GOOGLE_API_KEY",
             "GOOGLE_GENAI_API_KEY")

PROMPT = (
    "این فایل را **کامل و کلمه‌به‌کلمه** به متن برگردان — به همان زبانی که گفته می‌شود. "
    "خلاصه نکن، چیزی را جا نینداز، تکرارها و مکث‌ها را هم بنویس. هر حدودِ ۳۰ ثانیه یک برچسبِ زمان "
    "[hh:mm:ss] بگذار؛ اگر چند گوینده هست، گوینده‌ها را از هم جدا کن (گوینده ۱، گوینده ۲، …). "
    "صداهای غیرِگفتاری را در [کروشه] بنویس (موسیقی، سکوت، خنده). "
    "{video}"
    "وقتی واقعاً به آخرِ فایل رسیدی، در یک خطِ جدا دقیقاً بنویس: " + END
)
VIDEO_EXTRA = (
    "این یک ویدیو است: علاوه بر گفتار، در هر تغییرِ صحنه یک خطِ «[تصویر hh:mm:ss: …]» بنویس که "
    "دقیقاً چه چیزی روی صفحه دیده می‌شود، و هر نوشته‌ای که روی تصویر هست را **عیناً** بیاور. "
)
CONTINUE = ("ادامه بده — دقیقاً از همان‌جایی که متنِ قبلی‌ات تمام شد (آخرین بخش: «{tail}»)، "
            "بدونِ تکرار و بدونِ خلاصه، تا آخرِ فایل؛ و در پایان دقیقاً بنویس: " + END)
NO_KEY = ("کلیدِ Gemini برای رونویسی پیدا نشد — `GEMINI_API_KEY` را روی سرویس (Render) بگذار "
          "(یا در تنظیماتِ AI ِ همین سامانه)؛ بعد «خواندنِ دوباره»/`inspection.py pull`")


def find_key() -> Optional[str]:
    for provider in KEY_PROVIDERS:
        try:
            key = provider()
        except Exception:  # noqa: BLE001
            key = None
        if key:
            return key
    for env in _ENV_KEYS:
        if os.getenv(env):
            return os.getenv(env)
    return None


def _models(key: str) -> list[str]:
    """Preferred first: the configured model, then current Flash/Pro, then
    whatever this key can actually call (newest flash first)."""
    wanted = [m for m in (os.getenv("INSPECTION_TRANSCRIBE_MODEL"), "gemini-2.5-flash", "gemini-2.5-pro",
                          "gemini-2.0-flash") if m]
    try:
        listed = _get(f"{API}/v1beta/models?key={key}&pageSize=200").get("models") or []
        able = [m["name"].split("/", 1)[-1] for m in listed
                if "generateContent" in (m.get("supportedGenerationMethods") or [])
                and "gemini" in m.get("name", "") and not any(x in m["name"] for x in ("embedding", "tts", "image"))]
        flash = sorted((m for m in able if "flash" in m and "lite" not in m), reverse=True)
        return list(dict.fromkeys(wanted + flash + able))
    except Exception:  # noqa: BLE001 — listing is a convenience, not a requirement
        return wanted


def _req(url: str, *, data: Optional[bytes] = None, headers: Optional[dict] = None, method: str = "GET"):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def _get(url: str) -> dict:
    with _req(url) as r:
        return json.loads(r.read() or b"{}")


def _post_json(url: str, payload: dict) -> dict:
    with _req(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"},
              method="POST") as r:
        return json.loads(r.read() or b"{}")


def _upload(key: str, data: bytes, mime: str, name: str) -> dict:
    """Gemini Files API, resumable; waits until the file is ACTIVE."""
    with _req(f"{API}/upload/v1beta/files?key={key}", method="POST",
              data=json.dumps({"file": {"display_name": name[:100]}}).encode(),
              headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                       "X-Goog-Upload-Header-Content-Length": str(len(data)),
                       "X-Goog-Upload-Header-Content-Type": mime, "Content-Type": "application/json"}) as r:
        url = r.headers.get("x-goog-upload-url")
    if not url:
        raise IOError("Gemini نشانیِ آپلود نداد")
    with _req(url, data=data, method="POST",
              headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"}) as r:
        f = (json.loads(r.read() or b"{}")).get("file") or {}
    for _ in range(120):
        if f.get("state") in (None, "ACTIVE"):
            return f
        if f.get("state") == "FAILED":
            raise IOError("Gemini فایل را پردازش نکرد (FAILED)")
        time.sleep(5)
        f = _get(f"{API}/v1beta/{f['name']}?key={key}")
    raise IOError("پردازشِ فایل در Gemini تمام نشد (۱۰ دقیقه)")


def transcribe(data: bytes, filename: str, mime: str = "", *, api_key: Optional[str] = None) -> dict:
    """`{ok, text, note, truncated, model}` — the WHOLE transcript, or exactly why not."""
    import mimetypes

    key = api_key or find_key()
    if not key:
        return {"ok": False, "text": "", "note": NO_KEY, "truncated": False, "model": None}
    mime = (mime or mimetypes.guess_type(filename or "")[0] or "application/octet-stream").lower()
    video = mime.startswith("video/")
    uploaded = None
    last_err = ""
    try:
        if len(data) > INLINE_MAX:
            uploaded = _upload(key, data, mime, filename or "media")
            media = {"file_data": {"mime_type": mime, "file_uri": uploaded["uri"]}}
        else:
            media = {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}
        for model in _models(key):
            contents = [{"role": "user", "parts": [media, {"text": PROMPT.format(video=VIDEO_EXTRA if video else "")}]}]
            chunks: list[str] = []
            finished = False
            try:
                for _ in range(MAX_ROUNDS):
                    out = _post_json(f"{API}/v1beta/models/{model}:generateContent?key={key}",
                                     {"contents": contents,
                                      "generationConfig": {"temperature": 0, "maxOutputTokens": 65536}})
                    cand = (out.get("candidates") or [{}])[0]
                    piece = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", [])
                                    if isinstance(p, dict))
                    if END in piece:
                        chunks.append(piece.split(END)[0])
                        finished = True
                        break
                    if not piece.strip():
                        break
                    chunks.append(piece)
                    contents += [{"role": "model", "parts": [{"text": piece}]},
                                 {"role": "user", "parts": [{"text": CONTINUE.format(tail=piece.strip()[-200:])}]}]
            except urllib.error.HTTPError as e:
                last_err = f"{model}: HTTP {e.code} {e.read()[:200].decode('utf-8', 'replace')}"
                if e.code in (400, 404) and not chunks:
                    continue                      # this model cannot — try the next
                raise
            text = "".join(chunks).strip()
            if not text:
                last_err = f"{model}: پاسخِ خالی"
                continue
            note = (f"رونویسیِ کاملِ {'ویدیو (گفتار + شرحِ تصویر)' if video else 'صوت'} با {model}"
                    + ("" if finished else f" — به نشانِ پایان نرسید (سقفِ {MAX_ROUNDS} دور)؛ ممکن است انتها جا مانده باشد"))
            return {"ok": True, "text": text, "note": note, "truncated": not finished, "model": model}
        return {"ok": False, "text": "", "truncated": False, "model": None,
                "note": f"رونویسی نشد — هیچ مدلی جواب نداد ({last_err[:300]})"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "text": "", "truncated": False, "model": None,
                "note": f"رونویسی شکست خورد: {type(exc).__name__}: {exc}"[:400]}
    finally:
        if uploaded and uploaded.get("name"):
            try:
                _req(f"{API}/v1beta/{uploaded['name']}?key={key}", method="DELETE").close()
            except Exception:  # noqa: BLE001 — Gemini expires it in 48 h anyway
                pass


def transcribe_zip_members(data: bytes, *, api_key: Optional[str] = None) -> list[tuple[str, dict]]:
    """Full transcripts of the audio/video INSIDE an archive (recursively)."""
    import io
    import mimetypes
    import zipfile

    out = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            mime = mimetypes.guess_type(info.filename)[0] or ""
            if mime.startswith(("audio/", "video/")) or info.filename.lower().endswith(_MEDIA_EXT):
                out.append((info.filename, transcribe(z.read(info), info.filename, mime, api_key=api_key)))
            elif info.filename.lower().endswith(".zip"):
                out += [(f"{info.filename}/{n}", r) for n, r in transcribe_zip_members(z.read(info), api_key=api_key)]
    return out


def finish_extraction(ex: dict, data: bytes, filename: str, mime: str = "") -> dict:
    """Take an extract() result that is `pending` (audio/video, or an archive
    holding some) to its final form: the full transcript appended/used."""
    if ex.get("status") != "pending":
        return ex
    if (filename or "").lower().endswith(".zip"):
        text, truncated, ok, media = ex.get("text") or "", bool(ex.get("truncated")), 0, transcribe_zip_members(data)
        for name, res in media:
            ok += bool(res["ok"])
            text += f"\n\n===== رونویسیِ کاملِ {name} =====\n" + (res["text"] if res["ok"] else f"[{res['note']}]")
            truncated = truncated or bool(res.get("truncated"))
        note = (ex.get("note") or "") + f" — {ok} از {len(media)} صوت/ویدیوی داخلش کامل رونویسی شد"
        return {**ex, "status": "ok", "text": text, "note": note, "truncated": truncated}
    res = transcribe(data, filename, mime)
    if res["ok"]:
        return {**ex, "status": "ok", "text": res["text"], "note": res["note"], "truncated": res["truncated"]}
    # «failed», not «pending»: the reason is written and the sheet can still be
    # answered (needs-owner) — a permanent debt would jam the queue
    return {**ex, "status": "failed", "text": "", "note": res["note"]}
