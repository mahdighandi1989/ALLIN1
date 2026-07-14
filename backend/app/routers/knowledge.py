"""Knowledge Base API — the dynamic (AI-fed + manual) part of the دانش‌نامه.

GET  /api/knowledge/           → topics grouped by category, entries with refs
POST /api/knowledge/entries    → manual add (topic auto-grouped/created)
DELETE /api/knowledge/entries/{id} and /topics/{id} → soft delete
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.kb import KnowledgeTopic, KnowledgeEntry
from app.services import kb_store
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
                    "entries": ents})
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
