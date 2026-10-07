"""Knowledge Base API — the dynamic (AI-fed + manual) part of the دانش‌نامه.

GET  /api/knowledge/           → topics grouped by category, entries with refs
POST /api/knowledge/entries    → manual add (topic auto-grouped/created)
DELETE /api/knowledge/entries/{id} and /topics/{id} → soft delete
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.kb import KnowledgeTopic, KnowledgeEntry
from app.models.kb_chat import KbChatFile, KbChatMessage, KbChatSession
from app.services import kb_store, kb_chat, inspection_files
from app.services.audit import record_audit
from app.routers.auth import get_current_active_user, require_editor

router = APIRouter()


@router.get("/")
async def list_kb(db: AsyncSession = Depends(get_db), user=Depends(get_current_active_user)):
    topics = (await db.execute(
        select(KnowledgeTopic).where(KnowledgeTopic.is_deleted == False)  # noqa: E712
        .order_by(KnowledgeTopic.created_at)
    )).scalars().all()
    entries = (await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.is_deleted == False)  # noqa: E712
        .order_by(KnowledgeEntry.created_at)
    )).scalars().all()
    by_topic: dict = {}
    for e in entries:
        by_topic.setdefault(e.topic_id, []).append({
            "id": e.id, "content": e.content, "source_kind": e.source_kind,
            "source_ref": e.source_ref, "account_no": e.account_no,
            "created_by": e.created_by,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    out = []
    for t in topics:
        ents = by_topic.get(t.id, [])
        if not ents:
            continue  # an emptied topic disappears from the index automatically
        out.append({"id": t.id, "title": t.title, "category": t.category or "عمومی",
                    "tab": t.tab or kb_store.DEFAULT_TAB, "entries": ents})
    # the live index: categories in first-seen order, topics under each
    categories: list = []
    for t in out:
        if t["category"] not in categories:
            categories.append(t["category"])
    return {"topics": out, "categories": categories, "count": len(out)}


class KbEntryCreate(BaseModel):
    topic_title: str = Field(min_length=2, max_length=300)
    content: str = Field(min_length=3)
    category: str = ""
    source_ref: str = ""
    account_no: Optional[str] = None


@router.post("/entries")
async def add_entry(payload: KbEntryCreate, db: AsyncSession = Depends(get_db),
                    user=Depends(require_editor)):
    r = await kb_store.upsert_entry(
        db, topic_title=payload.topic_title, content=payload.content,
        category=payload.category, source_kind="manual",
        source_ref=payload.source_ref, account_no=payload.account_no or "",
        username=getattr(user, "username", "") or "",
    )
    if not r.get("ok"):
        raise HTTPException(status_code=422, detail="عنوان یا محتوا خالی است")
    await db.commit()
    return r


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, db: AsyncSession = Depends(get_db),
                       user=Depends(require_editor)):
    e = (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))).scalar_one_or_none()
    if e is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    e.is_deleted = True
    await db.commit()
    return {"ok": True}


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, db: AsyncSession = Depends(get_db),
                       user=Depends(require_editor)):
    t = (await db.execute(select(KnowledgeTopic).where(KnowledgeTopic.id == topic_id))).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    t.is_deleted = True
    for e in (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.topic_id == topic_id))).scalars():
        e.is_deleted = True
    await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# گفت‌وگو با دانش‌نامه — see app/services/kb_chat.py for the flow
# ---------------------------------------------------------------------------
def _is_admin(user) -> bool:
    return bool(getattr(user, "is_admin", False)) or getattr(user, "role", "") == "admin"


async def _own_session(db: AsyncSession, session_id: str, user) -> KbChatSession:
    sess = await db.get(KbChatSession, session_id)
    if sess is None or sess.is_deleted:
        raise HTTPException(status_code=404, detail="گفت‌وگو پیدا نشد")
    if not _is_admin(user) and sess.created_by != (getattr(user, "username", "") or ""):
        raise HTTPException(status_code=404, detail="گفت‌وگو پیدا نشد")
    return sess


@router.get("/chat/models")
async def chat_models(db: AsyncSession = Depends(get_db), user=Depends(get_current_active_user)):
    """Usable models, best default first (fast + web search + reads any file +
    cheap), derived from the live model rows — the daily sync keeps it current."""
    from app.ai import model_sync
    out = await kb_chat.ranked_models(db)
    out["sync"] = await model_sync.status(db)
    out["limits"] = {"max_file_mb": kb_chat.MAX_FILE_MB, "max_request_mb": kb_chat.MAX_REQUEST_MB,
                     "max_files": kb_chat.MAX_FILES}
    return out


@router.get("/chat/sessions")
async def chat_sessions(db: AsyncSession = Depends(get_db), user=Depends(get_current_active_user)):
    q = select(KbChatSession).where(KbChatSession.is_deleted == False)  # noqa: E712
    if not _is_admin(user):
        q = q.where(KbChatSession.created_by == (getattr(user, "username", "") or ""))
    rows = (await db.execute(q.order_by(KbChatSession.updated_at.desc().nullslast(),
                                        KbChatSession.created_at.desc()).limit(200))).scalars().all()
    return {"sessions": [{"id": r.id, "title": r.title or "گفت‌وگوی جدید", "created_by": r.created_by,
                          "created_at": r.created_at.isoformat() if r.created_at else None,
                          "updated_at": (r.updated_at or r.created_at).isoformat() if (r.updated_at or r.created_at) else None}
                         for r in rows]}


@router.get("/chat/sessions/{session_id}")
async def chat_session(session_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_active_user)):
    sess = await _own_session(db, session_id, user)
    msgs = (await db.execute(select(KbChatMessage).where(KbChatMessage.session_id == sess.id)
                             .order_by(KbChatMessage.created_at))).scalars().all()
    files = (await db.execute(select(KbChatFile).where(KbChatFile.session_id == sess.id)
                              .order_by(KbChatFile.created_at))).scalars().all()
    return {"session": {"id": sess.id, "title": sess.title or "", "created_by": sess.created_by},
            "messages": [kb_chat.message_public(m) for m in msgs],
            "files": [kb_chat.file_public(f) for f in files]}


@router.post("/chat/ask")
async def chat_ask(
    request: Request,
    question: str = Form(...),
    session_id: str = Form(""),
    model_id: Optional[int] = Form(None),
    allow_web: bool = Form(True),
    files: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    question = (question or "").strip()
    if len(question) < 2:
        raise HTTPException(status_code=422, detail="پرسش خالی است")
    username = getattr(user, "username", "") or ""
    if session_id:
        sess = await _own_session(db, session_id, user)
    else:
        sess = KbChatSession(created_by=username)
        db.add(sess)
        await db.flush()
    uploads = [f for f in (files or []) if f is not None and (f.filename or "")]
    if len(uploads) > kb_chat.MAX_FILES:
        raise HTTPException(status_code=413, detail=f"حداکثر {kb_chat.MAX_FILES} فایل در هر پیام")

    # Read every upload IN FULL (chunked, so an over-limit file is refused before
    # it is held whole), extract its text verbatim, put the bytes on Drive.
    per_file = kb_chat.MAX_FILE_MB * 1024 * 1024
    per_req = kb_chat.MAX_REQUEST_MB * 1024 * 1024
    total = 0
    new_files: List[KbChatFile] = []
    native: dict = {}
    for up in uploads:
        buf = bytearray()
        while True:
            chunk = await up.read(1024 * 1024)
            if not chunk:
                break
            buf += chunk
            if len(buf) > per_file:
                raise HTTPException(status_code=413, detail=f"«{up.filename}» از {kb_chat.MAX_FILE_MB} مگابایت بزرگ‌تر است")
        total += len(buf)
        if total > per_req:
            raise HTTPException(status_code=413, detail=f"مجموعِ فایل‌ها از {kb_chat.MAX_REQUEST_MB} مگابایت بیشتر است")
        data = bytes(buf)
        del buf
        row = await kb_chat.ingest_file(db, session_id=sess.id, filename=up.filename or "file",
                                        mime=up.content_type or "", data=data, username=username)
        new_files.append(row)
        if row.extract_status in ("image", "unsupported", "failed") and len(data) <= kb_chat.NATIVE_BYTES_CAP:
            native[row.id] = data
        del data
    await db.commit()          # the question and the files are on record even if the model call fails

    result = await kb_chat.answer_question(
        db, session=sess, question=question, model_id=model_id, allow_web=allow_web,
        new_files=new_files, native=native, username=username)
    await db.commit()

    a = result["assistant"]
    await record_audit(
        action="create", entity_type="kb_chat", entity_id=sess.id,
        detail=(f"پرسش: {question[:300]} | پاسخ از: {a['source'] or 'خطا'}"
                f"{' (وب: ' + a['web_model_name'] + ')' if a['web_model_name'] else ''} | مدل: {a['model_name'] or '—'}"
                f"{' | فایل: ' + '، '.join(f.filename for f in new_files) if new_files else ''}"
                f" | پاسخ: {a['content'][:300]}"),
        user=user, request=request, db=db)
    return {"session_id": sess.id, **result, "files": [kb_chat.file_public(f) for f in new_files]}


class ApproveBody(BaseModel):
    model_id: Optional[int] = None
    tab: str = ""


@router.post("/chat/messages/{message_id}/approve")
async def chat_approve(message_id: str, body: ApproveBody, request: Request,
                       db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    msg = await db.get(KbChatMessage, message_id)
    if msg is not None:
        await _own_session(db, msg.session_id, user)
    r = await kb_chat.file_web_answer(db, message_id=message_id, model_id=body.model_id,
                                      tab_override=body.tab, username=getattr(user, "username", "") or "")
    if not r.get("ok"):
        status = int(r.pop("status", 400))
        if r.get("error") == "tab_unclear":
            return Response(content=json.dumps(r, ensure_ascii=False), status_code=status,
                            media_type="application/json")
        raise HTTPException(status_code=status, detail=r.get("error") or "ناموفق")
    await db.commit()
    if not r.get("already"):
        await record_audit(
            action="create", entity_type="knowledge", entity_id=r.get("entry_id") or r.get("topic_id"),
            detail=f"ثبت پاسخِ وب در دانش‌نامه: {r.get('placement')}{' (تکراری — مطلبِ موجود)' if r.get('duplicate') else ''}",
            user=user, request=request, db=db)
    return r


@router.get("/chat/files/{file_id}/raw")
async def chat_file_raw(file_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_active_user)):
    f = await db.get(KbChatFile, file_id)
    if f is None:
        raise HTTPException(status_code=404, detail="فایل پیدا نشد")
    await _own_session(db, f.session_id, user)
    try:
        data = await inspection_files.load(f)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=410, detail=str(exc)[:200])
    from urllib.parse import quote
    return Response(content=data, media_type=f.mime or "application/octet-stream",
                    headers={"content-disposition": "attachment; filename*=UTF-8''" + quote(f.filename)})
