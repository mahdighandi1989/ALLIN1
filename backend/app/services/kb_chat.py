"""Knowledge-Base chat — the brain: context, model ranking, answering, filing.

Flow of one question (see routers/knowledge.py for the HTTP shell):

  1. files attached → each is read IN FULL (inspection_files.extract — no
     summarising), kept verbatim in the DB, and mirrored to Drive under a coded
     name; images / scanned PDFs travel to the model natively;
  2. STAGE A «دانش‌نامه»: the model sees the whole KB (static tabs + dynamic
     entries) and the files, and must answer ONLY from them — or begin with
     ``[[NOT_IN_KB]]``;
  3. STAGE B «وب»: only on that marker (and only if the user allows it), a
     web-capable model answers with live search and cites sources. That answer is
     stored as ``kb_state='pending'`` — it enters the KB only when the owner
     presses «تأیید» (:func:`file_web_answer`), where AI analyses it and files it
     under the right tab / category / topic.

Honesty rules this module keeps (each one a lesson in experiences/):
  * nothing is silently truncated — a file that does not fit the model's window
    stops the call and says so (silent-input-truncation…); a KB that does not fit
    is RANKED, trimmed, and the trim is reported;
  * a file the chosen model cannot read is NAMED as unread, never skipped quietly;
  * the model list is DERIVED from the live ai_models rows each time, so the daily
    model sync keeps it current without anyone editing a list (a-hand-maintained-
    list-rots-silently).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import ai_manager, catalog
from app.ai import chat as ai_chat
from app.ai.tester import _family, drop_superseded
from app.models.ai_config import AIModel, AIProvider
from app.models.kb import KnowledgeEntry, KnowledgeTopic
from app.models.kb_chat import (
    KB_FILED, KB_NONE, KB_PENDING, SOURCE_KB, SOURCE_NONE, SOURCE_WEB,
    KbChatFile, KbChatMessage, KbChatSession,
)
from app.services import inspection_files, kb_store

logger = logging.getLogger("app.kb_chat")

NOT_IN_KB = "[[NOT_IN_KB]]"

#: Per-file / per-request ceilings (bytes). The owner asked for «حداکثر حجم مقدور»;
#: the container has 512 MB of RAM, so the defaults are 50 MB a file / 100 MB a
#: request and an operator on a bigger plan can raise them.
MAX_FILE_MB = int(os.getenv("KB_CHAT_MAX_FILE_MB", "50"))
MAX_REQUEST_MB = int(os.getenv("KB_CHAT_MAX_REQUEST_MB", "100"))
MAX_FILES = int(os.getenv("KB_CHAT_MAX_FILES", "12"))
#: Total bytes of images / scanned PDFs one request may carry natively (provider
#: request limits sit near 32 MB once base64 inflates the data by a third).
NATIVE_BYTES_CAP = 20 * 1024 * 1024
#: Persian runs ~2 characters per token in the worst tokenizers — assume that.
CHARS_PER_TOKEN = 2.0
KB_CHARS_CAP = int(os.getenv("KB_CHAT_KB_CHARS", "600000"))
HISTORY_TURNS = 6

_NON_CHAT = re.compile(r"embed|tts|audio|whisper|transcribe|moderation|realtime|image|dall|imagen|veo|video|rerank", re.I)
_FAST_NAME = re.compile(r"mini|nano|flash|haiku|lite|small|turbo|fast", re.I)


# ---------------------------------------------------------------------------
# The KB as text
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_static() -> Dict[str, Any]:
    """The static tabs, exported from the TypeScript source by
    frontend/scripts/export-kb.mjs (run by `npm run build`)."""
    p = Path(__file__).resolve().parent.parent / "data" / "kb_static.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.error("kb_static.json unreadable: %s", exc)
        return {"tabs": [], "compare": []}


def tab_labels() -> Dict[str, str]:
    return {t["id"]: t["label"] for t in load_static().get("tabs", [])}


def _toks(s: str) -> set:
    s = kb_store.norm_title(s)
    return {w for w in re.findall(r"[\w؀-ۿ]{2,}", s) if not w.isdigit()}


async def kb_sections(db: AsyncSession) -> List[Dict[str, Any]]:
    """Every KB unit as {ref, text}: static sections, compare rows, dynamic topics."""
    out: List[Dict[str, Any]] = []
    for t in load_static().get("tabs", []):
        for s in t.get("sections", []):
            out.append({"ref": f"{t['label']} › {s['title']}", "text": s.get("text", "")})
    for r in load_static().get("compare", []):
        out.append({"ref": f"تطبیق › {r['topic']} ({r['verdict']})", "text": r.get("text", "")})
    labels = tab_labels()
    topics = (await db.execute(select(KnowledgeTopic).where(KnowledgeTopic.is_deleted == False))).scalars().all()  # noqa: E712
    entries = (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.is_deleted == False)  # noqa: E712
                                .order_by(KnowledgeEntry.created_at))).scalars().all()
    by_topic: Dict[str, list] = {}
    for e in entries:
        by_topic.setdefault(e.topic_id, []).append(e)
    for tp in topics:
        ents = by_topic.get(tp.id, [])
        if not ents:
            continue
        label = labels.get(tp.tab or kb_store.DEFAULT_TAB, tp.tab or "")
        body = "\n\n".join(f"{e.content}\n(منبع: {e.source_ref or '—'})" for e in ents)
        out.append({"ref": f"{label} › {tp.category or 'عمومی'} › {tp.title}", "text": body})
    return out


def build_kb_context(sections: List[Dict[str, Any]], question: str, budget_chars: int) -> Tuple[str, Dict[str, Any]]:
    """The KB as one prompt block. Whole KB when it fits; otherwise the best-matching
    sections up to the budget — plus a title index of EVERYTHING so the model can
    tell what exists — and the cut is reported in the returned meta."""
    total_chars = sum(len(s["text"]) + len(s["ref"]) + 10 for s in sections)
    meta = {"total_sections": len(sections), "total_chars": total_chars}
    if total_chars <= budget_chars:
        chosen = sections
        trimmed = False
    else:
        q = _toks(question)
        scored = sorted(sections, key=lambda s: -len(q & _toks(s["ref"] + " " + s["text"])))
        chosen, used = [], 0
        for s in scored:
            c = len(s["text"]) + len(s["ref"]) + 10
            if used + c > budget_chars:
                continue
            chosen.append(s)
            used += c
        keep = {id(s) for s in chosen}
        chosen = [s for s in sections if id(s) in keep]      # original (page) order
        trimmed = True
    parts = [f"### [{s['ref']}]\n{s['text']}" for s in chosen]
    block = "\n\n".join(parts)
    if trimmed:
        block += ("\n\n--- فهرستِ عنوانِ همهٔ بخش‌های دانش‌نامه (متنِ بخش‌های بالا فقط به‌دلیلِ حجم انتخاب شد) ---\n"
                  + "\n".join(f"- {s['ref']}" for s in sections))
    meta.update(included_sections=len(chosen), trimmed=trimmed, chars=len(block))
    return block, meta


# ---------------------------------------------------------------------------
# Models — ranked from live rows
# ---------------------------------------------------------------------------
def _cost_points(inp: Optional[float]) -> int:
    if inp is None:
        return 0
    if inp <= 1:
        return 3
    if inp <= 3:
        return 2
    if inp <= 10:
        return 1
    return -1 if inp > 30 else 0


def score_model(m: AIModel, provider: AIProvider) -> Tuple[int, Dict[str, Any]]:
    """Default-ordering score: fast + web-search + reads-any-file + cheap. Derived
    purely from the row (capabilities, provider, price, name), so a model the daily
    sync just discovered ranks itself."""
    caps = set(m.capabilities or [])
    base_url = provider.base_url or catalog.PROVIDER_CATALOG.get(provider.key, {}).get("base_url") or ""
    fast = "fast" in caps or bool(_FAST_NAME.search(m.api_id or ""))
    web = ai_chat.supports_web(provider.key, base_url, list(caps), m.api_id)
    docs = "documents" in caps
    vision = "vision" in caps or docs
    cheap_pts = _cost_points(m.input_cost_per_1m)
    score = (3 if fast else 0) + (3 if web else 0) + (2 if docs else (1 if vision else 0)) + cheap_pts
    if m.context_window and m.context_window >= 200000:
        score += 1
    return score, {"fast": fast, "web": web, "files": docs, "vision": vision,
                   "cheap": cheap_pts >= 2, "price_known": m.input_cost_per_1m is not None}


async def ranked_models(db: AsyncSession) -> Dict[str, Any]:
    """Usable chat models, best default first. ``default_model_id`` is the top one."""
    providers = {p.key: p for p in (await db.execute(select(AIProvider))).scalars()}
    rows = (await db.execute(select(AIModel).where(AIModel.enabled.is_(True)))).scalars().all()
    items = []
    for m in rows:
        p = providers.get(m.provider_key)
        if p is None or not p.enabled or not ai_manager.provider_configured(p):
            continue
        if _NON_CHAT.search(m.api_id or "") or "text" not in set(m.capabilities or ["text"]):
            continue
        score, flags = score_model(m, p)
        items.append({
            "id": m.id, "display_name": m.display_name, "provider_key": m.provider_key,
            "provider_name": p.display_name, "api_model_id": m.api_id,
            "capabilities": list(m.capabilities or []), "priority": m.priority,
            "context_window": m.context_window, "input_cost_per_1m": m.input_cost_per_1m,
            "output_cost_per_1m": m.output_cost_per_1m, "score": score, **flags,
        })
    items = drop_superseded(items)          # current generation only (picker view)
    items.sort(key=lambda x: (-x["score"], x["priority"], x["display_name"]))
    top = items[0]["score"] if items else 0
    for it in items:
        it["recommended"] = bool(it["web"] and it["fast"] and it["score"] >= max(top - 2, 1))
    return {"models": items, "default_model_id": items[0]["id"] if items else None}


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
def _is_pdf(name: str, mime: str) -> bool:
    return (mime or "").lower() == "application/pdf" or (name or "").lower().endswith(".pdf")


async def ingest_file(db: AsyncSession, *, session_id: str, filename: str, mime: str,
                      data: bytes, username: str) -> KbChatFile:
    """Read ONE upload in full, keep the text verbatim, put the bytes on Drive."""
    ex = await asyncio.to_thread(inspection_files.extract, data, filename, mime)
    name = inspection_files.safe_filename(filename)
    stem, _, ext = name.rpartition(".") if "." in name else (name, "", "")
    from app.services import drive_sync
    coded = drive_sync.build_name("kbchat", session_id, stem or name, ext, unicode_descriptor=True)
    st = await inspection_files.store(
        data=data, filename=name, mime=mime, path_parts=["knowledge-chat", session_id],
        stored_name=coded, local_prefix=f"kbchat-{session_id}-")
    text = ex.get("text") or ""
    row = KbChatFile(
        session_id=session_id, filename=name, mime=mime or "", byte_size=len(data),
        sha256=st.get("sha256", ""), extract_status=ex.get("status", ""),
        extract_note=ex.get("note", ""), text=text, text_chars=len(text),
        truncated=bool(ex.get("truncated")), store=st.get("store", ""),
        drive_id=st.get("drive_id", ""), drive_link=st.get("drive_link", ""),
        local_path=st.get("local_path", ""), store_note=st.get("store_note", ""),
        created_by=username)
    db.add(row)
    await db.flush()
    return row


def file_public(f: KbChatFile) -> Dict[str, Any]:
    return {"id": f.id, "message_id": f.message_id, "filename": f.filename, "mime": f.mime,
            "byte_size": f.byte_size, "extract_status": f.extract_status, "note": f.extract_note or "",
            "text_chars": f.text_chars or 0, "truncated": bool(f.truncated), "store": f.store,
            "drive_link": f.drive_link or "", "durable": f.store == "drive",
            "store_note": f.store_note or ""}


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
KB_SYSTEM = f"""تو دستیار «دانش‌نامهٔ عملیات بانکی» (دایره تسهیلات اعطایی — بانک صادرات ایران، سرپرستی امارات) هستی.
به فارسیِ روان و دقیق پاسخ بده؛ اصطلاحاتِ تخصصی بانکی را در صورت لزوم به انگلیسی نگه دار.

قواعد (الزام‌آور):
۱. فقط بر پایهٔ «دانش‌نامه» و «فایل‌های پیوست» همین پیام پاسخ بده. از دانشِ عمومیِ خودت برای تکمیلِ پاسخ استفاده نکن و چیزی را حدس نزن.
۲. اگر دانش‌نامه و فایل‌ها پاسخِ اصلِ پرسش را ندارند، پاسخت را دقیقاً با نشانهٔ {NOT_IN_KB} در سطرِ اولِ جداگانه شروع کن و پس از آن در یک جمله بگو چه چیزی در دانش‌نامه نبود.
۳. وقتی از دانش‌نامه پاسخ می‌دهی، در پایان یک سطر بنویس «منبع در دانش‌نامه: …» با نامِ تب و عنوانِ بخش‌هایی که به کار بردی.
۴. فایل‌های پیوست کامل و بدونِ خلاصه داده شده‌اند؛ هر ادعا دربارهٔ آن‌ها باید از متنِ دقیقشان باشد. اگر فایلی «خوانده‌نشده» اعلام شده، همین را به کاربر بگو و دربارهٔ محتوایش حدس نزن.
۵. پاسخ کامل و دقیق باشد؛ ارقام، نرخ‌ها، تاریخ‌ها و نام‌ها را عیناً از منبع بیاور."""

WEB_SYSTEM = """تو دستیار «دانش‌نامهٔ عملیات بانکی» (بانک صادرات ایران، سرپرستی امارات) هستی. پاسخِ این پرسش در دانش‌نامه نبود و حالا باید با جستجوی زندهٔ وب پاسخ بدهی.
به فارسیِ روان و دقیق بنویس. به منابعِ رسمی (بانک مرکزی، متنِ قانون/بخشنامه، نهادهای بین‌المللی) اولویت بده، تاریخِ منبع را بررسی کن و اگر موضوع به‌روز نیست یا منابع با هم نمی‌خوانند، صریح بگو. ارقام و نام‌ها را عیناً از منبع بیاور و حدس نزن. اگر فایل پیوست هست، پرسش دربارهٔ آن‌هاست و متن‌شان کامل در پیام آمده است. در پایان، منبع‌ها را فهرست کن."""

FILE_SYSTEM = """تو دستیارِ دانش‌نامه‌ای. فقط یک شیءِ JSON معتبر برگردان، بدونِ هیچ متنِ دیگر."""


def _approx_tokens(chars: int) -> int:
    return int(chars / CHARS_PER_TOKEN)


def _usable_chars(resolved) -> int:
    ctx = resolved.context_window or 128_000
    out = min(resolved.max_output_tokens or 8000, 8000)
    return int(max(ctx * 0.8 - out, 8000) * CHARS_PER_TOKEN)


def _history_turns(messages: List[KbChatMessage]) -> List[Dict[str, str]]:
    turns: List[Dict[str, str]] = []
    for m in messages[-HISTORY_TURNS:]:
        txt = (m.content or "")[:3000]
        if m.role == "assistant" and m.source == SOURCE_NONE and m.error:
            continue
        turns.append({"role": "user" if m.role == "user" else "assistant", "content": txt})
    # providers require the first turn to be a user turn and roles to alternate
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    merged: List[Dict[str, str]] = []
    for t in turns:
        if merged and merged[-1]["role"] == t["role"]:
            merged[-1]["content"] += "\n\n" + t["content"]
        else:
            merged.append(dict(t))
    if merged and merged[-1]["role"] == "user":
        merged.pop()                # the new question follows; avoid user→user
    return merged


# ---------------------------------------------------------------------------
# The question
# ---------------------------------------------------------------------------
async def answer_question(
    db: AsyncSession, *, session: KbChatSession, question: str, model_id: Optional[int],
    allow_web: bool, new_files: List[KbChatFile], native: Dict[str, bytes], username: str,
) -> Dict[str, Any]:
    """Answer one question. Returns the assistant message dict (already stored)."""
    history_rows = (await db.execute(select(KbChatMessage).where(KbChatMessage.session_id == session.id)
                                     .order_by(KbChatMessage.created_at))).scalars().all()
    q_msg = KbChatMessage(session_id=session.id, role="user", content=question, created_by=username,
                          meta={"file_ids": [f.id for f in new_files]})
    db.add(q_msg)
    await db.flush()
    for f in new_files:
        f.message_id = q_msg.id

    def fail(error: str, *, source: str = SOURCE_NONE, model: str = "", meta: Optional[dict] = None) -> KbChatMessage:
        m = KbChatMessage(session_id=session.id, role="assistant", content=error, source=source,
                          model_name=model, error=error, meta=meta or {}, created_by=username)
        db.add(m)
        return m

    # ---- resolve the model ------------------------------------------------
    resolved = None
    if model_id is not None:
        resolved = await ai_manager.resolve_specific(db, model_id, "chat")
        if resolved is None or not resolved.is_usable:
            m = fail("مدلِ انتخاب‌شده در دسترس نیست (غیرفعال یا بدونِ کلید). مدلِ دیگری انتخاب کنید.")
            await db.flush()
            return await _finish(db, session, q_msg, m, question)
    if resolved is None:
        rank = await ranked_models(db)
        if rank["default_model_id"] is not None:
            resolved = await ai_manager.resolve_specific(db, rank["default_model_id"], "chat")
    if resolved is None or not resolved.is_usable:
        m = fail("هیچ مدلِ هوش مصنوعیِ فعال و دارای کلید تنظیم نشده است — از «تنظیمات › مدل‌های هوش مصنوعی» یک ارائه‌دهنده فعال کنید.")
        await db.flush()
        return await _finish(db, session, q_msg, m, question)

    caps = set(resolved.capabilities or [])
    fam = _family(resolved.provider_key, resolved.base_url or "")
    can_pdf = ("documents" in caps) or fam in ("anthropic", "gemini")
    can_img = ("vision" in caps) or can_pdf

    # ---- files: this turn's (required) + earlier session files (as budget allows)
    warnings: List[str] = []
    native_files: List[Dict[str, Any]] = []
    native_used = 0
    text_blocks: List[Tuple[str, str]] = []
    unread: List[str] = []
    for f in new_files:
        if f.extract_status == "ok" and f.text:
            text_blocks.append((f.filename, f.text))
            if f.truncated:
                warnings.append(f"متنِ «{f.filename}» از سقفِ ذخیره بزرگ‌تر بود و کامل نیست")
        elif f.id in native:
            is_img = (f.mime or "").lower().startswith("image/") or f.extract_status == "image"
            ok_native = can_img if is_img else (can_pdf and _is_pdf(f.filename, f.mime))
            if ok_native and native_used + len(native[f.id]) <= NATIVE_BYTES_CAP:
                mt = (f.mime or ("application/pdf" if _is_pdf(f.filename, "") else "image/png")).lower()
                native_files.append({"filename": f.filename, "mimetype": mt, "data": native[f.id]})
                native_used += len(native[f.id])
            else:
                unread.append(f"{f.filename} — " + ("مدلِ انتخاب‌شده تصویر/PDFِ اسکن را نمی‌خواند" if not ok_native
                                                     else "حجمِ فایل‌های تصویری/اسکن از سقفِ ارسال بیشتر است"))
        else:
            unread.append(f"{f.filename} — {f.extract_note or 'قالبِ فایل پشتیبانی نمی‌شود'}")
    old_files = (await db.execute(select(KbChatFile).where(KbChatFile.session_id == session.id,
                                                           KbChatFile.id.notin_([f.id for f in new_files] or [""]))
                                  .order_by(KbChatFile.created_at.desc()))).scalars().all()

    budget = _usable_chars(resolved)
    files_chars = sum(len(t) for _, t in text_blocks)
    hist = _history_turns(history_rows)
    hist_chars = sum(len(t["content"]) for t in hist)
    overhead = 12_000 + len(question)
    if files_chars + hist_chars + overhead > budget:
        names = ", ".join(n for n, _ in text_blocks)
        m = fail(f"متنِ کاملِ فایل(ها) ({files_chars:,} نویسه: {names}) از ظرفیتِ مدلِ «{resolved.display_name}» "
                 f"(حدود {budget:,} نویسه) بیشتر است. برای اینکه فایل «کامل» خوانده شود و چیزی بی‌صدا بریده نشود، "
                 "مدلی با پنجرهٔ بزرگ‌تر (مثلاً Gemini یا Claude با ۱ میلیون توکن) انتخاب کنید.",
                 model=resolved.display_name, meta={"files_chars": files_chars, "budget_chars": budget})
        await db.flush()
        return await _finish(db, session, q_msg, m, question)
    left = budget - files_chars - hist_chars - overhead
    omitted_old = []
    for f in old_files:
        if f.extract_status == "ok" and f.text:
            if len(f.text) <= max(left - 40_000, 0):
                text_blocks.append((f.filename + " (از پیام‌های قبلیِ همین گفت‌وگو)", f.text))
                left -= len(f.text)
                files_chars += len(f.text)
            else:
                omitted_old.append(f.filename)
        elif f.extract_status in ("image", "unsupported", "failed") and f.id not in {x.id for x in new_files}:
            omitted_old.append(f.filename)
    if omitted_old:
        warnings.append("در این نوبت ارسال نشد (جا یا نوعِ فایل): " + "، ".join(omitted_old))

    # ---- the KB, within what is left ----------------------------------------
    sections = await kb_sections(db)
    prev_q = next((m.content for m in reversed(history_rows) if m.role == "user"), "")
    kb_budget = max(min(left, KB_CHARS_CAP), 20_000)
    kb_text, kb_meta = build_kb_context(sections, f"{prev_q}\n{question}", kb_budget)

    def compose(with_kb: bool) -> str:
        blocks = []
        if with_kb:
            blocks.append("=== دانش‌نامه ===\n" + kb_text)
        if text_blocks:
            blocks.append("=== فایل‌های پیوست (متنِ کامل، بدونِ خلاصه) ===\n" + "\n\n".join(
                f"--- فایل: {n} ({len(t):,} نویسه) ---\n{t}" for n, t in text_blocks))
        if native_files:
            blocks.append("=== فایل‌های تصویری/اسکن‌شده: به‌صورتِ ضمیمهٔ همین پیام فرستاده شدند؛ آن‌ها را مستقیماً ببین ===\n"
                          + "\n".join(f"- {f['filename']}" for f in native_files))
        if unread:
            blocks.append("=== فایل‌های خوانده‌نشده (به کاربر بگو که این‌ها خوانده نشدند) ===\n" + "\n".join(f"- {u}" for u in unread))
        blocks.append("=== پرسش ===\n" + question)
        return "\n\n".join(blocks)

    meta: Dict[str, Any] = {"kb": kb_meta, "warnings": warnings, "unread_files": unread,
                            "file_ids": [f.id for f in new_files], "native_files": [f["filename"] for f in native_files],
                            "budget_chars": budget}
    turns = hist + [{"role": "user", "content": compose(True)}]
    max_out = min(resolved.max_output_tokens or 8000, 8000)

    # ---- STAGE A: from the KB / files ---------------------------------------
    ra = await ai_chat.chat(resolved, system=KB_SYSTEM, turns=turns, files=native_files, web=False, max_tokens=max_out)
    if not ra["ok"]:
        m = fail(f"فراخوانی مدل «{resolved.display_name}» ناموفق بود: {ra['error']}", model=resolved.display_name, meta=meta)
        await db.flush()
        return await _finish(db, session, q_msg, m, question)
    text = ra["text"].strip()
    head = text[:400]
    if NOT_IN_KB in head:
        not_in_kb_note = text.replace(NOT_IN_KB, "", 1).strip()
        meta["not_in_kb_note"] = not_in_kb_note
        if not allow_web:
            m = KbChatMessage(session_id=session.id, role="assistant", source=SOURCE_NONE, model_name=resolved.display_name,
                              content=(not_in_kb_note or "پاسخ در دانش‌نامه نبود.") + "\n\n(جستجوی وب خاموش بود.)",
                              meta=meta, created_by=username)
            db.add(m)
            await db.flush()
            return await _finish(db, session, q_msg, m, question)
        # ---- STAGE B: the web ------------------------------------------------
        web_resolved, why = await _pick_web_model(db, resolved)
        if web_resolved is None:
            m = KbChatMessage(session_id=session.id, role="assistant", source=SOURCE_NONE, model_name=resolved.display_name,
                              content=(not_in_kb_note or "پاسخ در دانش‌نامه نبود.") + "\n\nمدلی با قابلیتِ جستجوی وب (Claude با کلیدِ API، Gemini، Perplexity) فعال نیست؛ برای پاسخ از وب یکی را در تنظیمات فعال کنید.",
                              meta=meta, created_by=username)
            db.add(m)
            await db.flush()
            return await _finish(db, session, q_msg, m, question)
        meta["web_model_reason"] = why
        wturns = hist + [{"role": "user", "content":
                          compose(False) + f"\n\n(یادداشت: دانش‌نامه پاسخ نداشت — {not_in_kb_note[:300]})"}]
        rb = await ai_chat.chat(web_resolved, system=WEB_SYSTEM, turns=wturns, files=native_files if _can_native(web_resolved) else [],
                                web=True, max_tokens=min(web_resolved.max_output_tokens or 8000, 8000))
        if not rb["ok"]:
            m = KbChatMessage(session_id=session.id, role="assistant", source=SOURCE_NONE, model_name=resolved.display_name,
                              content=(not_in_kb_note or "پاسخ در دانش‌نامه نبود.") + f"\n\nجستجوی وب با «{web_resolved.display_name}» ناموفق بود: {rb['error']}",
                              error=rb["error"], meta=meta, created_by=username)
            db.add(m)
            await db.flush()
            return await _finish(db, session, q_msg, m, question)
        m = KbChatMessage(session_id=session.id, role="assistant", source=SOURCE_WEB, model_name=resolved.display_name,
                          web_model_name=web_resolved.display_name, content=rb["text"].strip(), sources=rb["sources"],
                          kb_state=KB_PENDING, meta=meta, created_by=username)
        db.add(m)
        await db.flush()
        return await _finish(db, session, q_msg, m, question)

    m = KbChatMessage(session_id=session.id, role="assistant", source=SOURCE_KB, model_name=resolved.display_name,
                      content=text, meta=meta, created_by=username)
    db.add(m)
    await db.flush()
    return await _finish(db, session, q_msg, m, question)


def _can_native(resolved) -> bool:
    caps = set(resolved.capabilities or [])
    return "vision" in caps or "documents" in caps or _family(resolved.provider_key, resolved.base_url or "") in ("anthropic", "gemini")


async def _pick_web_model(db: AsyncSession, chosen) -> Tuple[Optional[Any], str]:
    """The chosen model if it can search the web, else the best-ranked one that can."""
    if ai_chat.supports_web(chosen.provider_key, chosen.base_url or "", chosen.capabilities, chosen.model_key):
        return chosen, "مدلِ انتخاب‌شده خودش جستجوی وب دارد"
    for it in (await ranked_models(db))["models"]:
        if it["web"]:
            r = await ai_manager.resolve_specific(db, it["id"], "chat")
            if r is not None and r.is_usable:
                return r, f"مدلِ انتخاب‌شده جستجوی وب ندارد؛ به‌جایش «{r.display_name}» جستجو کرد"
    return None, ""


async def _finish(db: AsyncSession, session: KbChatSession, q_msg: KbChatMessage,
                  a_msg: KbChatMessage, question: str) -> Dict[str, Any]:
    if not (session.title or "").strip():
        session.title = re.sub(r"\s+", " ", question).strip()[:120]
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"user": message_public(q_msg), "assistant": message_public(a_msg)}


def message_public(m: KbChatMessage) -> Dict[str, Any]:
    return {"id": m.id, "session_id": m.session_id, "role": m.role, "content": m.content,
            "source": m.source or "", "model_name": m.model_name or "", "web_model_name": m.web_model_name or "",
            "sources": list(m.sources or []), "meta": m.meta or {}, "kb_state": m.kb_state or "",
            "kb_topic_id": m.kb_topic_id, "kb_placement": m.kb_placement or "", "error": m.error or "",
            "created_by": m.created_by, "created_at": m.created_at.isoformat() if m.created_at else None}


# ---------------------------------------------------------------------------
# Approve → AI analysis → filed in the KB
# ---------------------------------------------------------------------------
async def _taxonomy(db: AsyncSession) -> Dict[str, Any]:
    labels = tab_labels()
    tabs = []
    dyn = (await db.execute(select(KnowledgeTopic).where(KnowledgeTopic.is_deleted == False))).scalars().all()  # noqa: E712
    for t in load_static().get("tabs", []):
        tabs.append({"id": t["id"], "label": t["label"],
                     "sections": [s["title"] for s in t.get("sections", [])][:60],
                     "filed_topics": [{"category": d.category, "title": d.title} for d in dyn
                                      if (d.tab or kb_store.DEFAULT_TAB) == t["id"]][:80]})
    return {"tabs": tabs, "labels": labels}


def _filing_prompt(question: str, answer: str, tax: Dict[str, Any]) -> str:
    return f"""یک پرسش و پاسخِ مبتنی بر وب را باید در «دانش‌نامهٔ عملیات بانکی» ثبت کنی. تحلیل کن و فقط این JSON را برگردان:
{{"tab": "<یکی از: saderat | uae | intl | iran | islamic>",
 "category": "<نامِ دستهٔ فهرست؛ اگر دستهٔ مناسب از قبل در filed_topics هست دقیقاً همان را بیاور، وگرنه دستهٔ جدیدِ کوتاه بساز>",
 "topic_title": "<عنوانِ موضوع؛ اگر موضوعِ هم‌معنا از قبل هست دقیقاً همان عنوان، وگرنه عنوانِ تازهٔ کوتاه و گویا>",
 "content": "<متنِ دانش‌نامه‌ای: پاسخ را کامل و دقیق و بدونِ حذفِ هیچ عدد/نرخ/تاریخ/نام/شرط بازنویسی کن، به‌صورتِ مطلبِ آموزشیِ مستقل (نه گفت‌وگو)؛ بدونِ لیستِ منابع>"}}

تب‌ها: saderat = رویه‌های داخلیِ بانک صادرات/سرپرستی امارات؛ uae = قوانین و مقرراتِ بانک مرکزیِ امارات؛ intl = مقرراتِ جهانی (بازل، ICC، FATF، SWIFT)؛ iran = قوانین و مقرراتِ ایران؛ islamic = بانکداریِ اسلامی.
اگر مطلب به چند تب مربوط است، تبی را بیاور که موضوعِ اصلیِ پاسخ در آن است.

ساختارِ فعلیِ دانش‌نامه:
{json.dumps(tax['tabs'], ensure_ascii=False)}

پرسش:
{question}

پاسخ:
{answer}"""


async def file_web_answer(db: AsyncSession, *, message_id: str, model_id: Optional[int],
                          tab_override: str, username: str) -> Dict[str, Any]:
    from app.services.doc_ingest import parse_model_json
    from app.ai import inference

    msg = await db.get(KbChatMessage, message_id)
    if msg is None or msg.role != "assistant":
        return {"ok": False, "status": 404, "error": "پیام پیدا نشد"}
    if msg.source != SOURCE_WEB:
        return {"ok": False, "status": 422, "error": "فقط پاسخ‌هایی که از وب آمده‌اند به دانش‌نامه اضافه می‌شوند"}
    if msg.kb_state == KB_FILED:      # idempotent: a second click returns the placement
        return {"ok": True, "already": True, "placement": msg.kb_placement, "topic_id": msg.kb_topic_id,
                "entry_id": msg.kb_entry_id, "message": message_public(msg)}
    qrow = (await db.execute(select(KbChatMessage).where(
        KbChatMessage.session_id == msg.session_id, KbChatMessage.role == "user",
        KbChatMessage.created_at <= msg.created_at).order_by(KbChatMessage.created_at.desc()))).scalars().first()
    question = qrow.content if qrow else ""

    tab = kb_store.norm_tab(tab_override)
    parsed: Dict[str, Any] = {}
    tax = await _taxonomy(db)
    r = await inference.complete(db, _filing_prompt(question, msg.content, tax), task="general", system=FILE_SYSTEM,
                                 max_tokens=8000, model_id=model_id, timeout=180.0)
    if not r.get("ok"):
        return {"ok": False, "status": 502, "error": f"تحلیلِ هوش مصنوعی ناموفق بود: {r.get('error')}"}
    parsed = parse_model_json(r.get("text", ""))
    title = (parsed.get("topic_title") or "").strip()
    category = (parsed.get("category") or "").strip()
    content = (parsed.get("content") or "").strip()
    if not tab:
        tab = kb_store.norm_tab(parsed.get("tab", ""))
    if not tab:
        # never guess a tab: a wrong shelf is worse than asking (a-default-that-looks-like-a-decision…)
        return {"ok": False, "status": 409, "error": "tab_unclear",
                "message": "هوش مصنوعی تبِ مناسب را مشخص نکرد؛ یکی از تب‌ها را انتخاب کنید.",
                "tabs": [{"id": k, "label": v} for k, v in tab_labels().items()]}
    if not title or not content:
        return {"ok": False, "status": 502, "error": "تحلیلِ هوش مصنوعی عنوان یا متن نداد؛ دوباره تلاش کنید."}
    # a lossy rewrite must never replace the answer: if the model shortened it a lot, keep the original verbatim
    plain = re.sub(r"\s+", "", msg.content)
    if len(re.sub(r"\s+", "", content)) < 0.6 * len(plain):
        content = msg.content.strip()
    srcs = [s for s in (msg.sources or []) if isinstance(s, dict) and s.get("url")]
    footer = ""
    if srcs:
        footer = "\n\nمنابع وب:\n" + "\n".join(f"- {s.get('title') or s['url']}: {s['url']}" for s in srcs[:12])
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ref = f"گفت‌وگوی دانش‌نامه {stamp} — پاسخ از وب" + (f" ({srcs[0]['url']})" if srcs else "")
    res = await kb_store.upsert_entry(
        db, topic_title=title, content=content + footer, category=category or "عمومی", source_kind="chat_web",
        source_ref=ref[:400], username=username, global_dedupe=True, tab=tab)
    if not res.get("ok"):
        return {"ok": False, "status": 422, "error": "عنوان یا محتوا خالی است"}
    topic = await db.get(KnowledgeTopic, res["topic_id"])
    label = tab_labels().get(topic.tab or kb_store.DEFAULT_TAB, tab)
    placement = f"{label} › {topic.category or 'عمومی'} › {topic.title}"
    msg.kb_state = KB_FILED
    msg.kb_topic_id = res["topic_id"]
    msg.kb_entry_id = res.get("entry_id")
    msg.kb_placement = placement[:500]
    await db.flush()
    return {"ok": True, "already": False, "duplicate": bool(res.get("duplicate_global") or not res.get("created_entry")),
            "created_topic": res.get("created_topic"), "tab": topic.tab or kb_store.DEFAULT_TAB,
            "placement": placement, "topic_id": res["topic_id"], "entry_id": res.get("entry_id"),
            "message": message_public(msg)}
