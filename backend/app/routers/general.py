"""General (non-account) profiles + checklists + items — requirement A7.

A lightweight, generic checklist system for recurring topics that are not tied
to a specific customer account. Mounted at /api/general.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.general import GeneralProfile, GeneralChecklist, GeneralChecklistItem
from app.utils.security import get_current_user
from app.routers.auth import require_editor

router = APIRouter(tags=["general"], dependencies=[Depends(get_current_user)])


def _gid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


# --- profiles ---------------------------------------------------------------
class ProfileCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: str = ""


@router.get("/profiles")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(GeneralProfile).where(GeneralProfile.is_deleted == False).order_by(GeneralProfile.created_at.desc())  # noqa: E712
        )
    ).scalars().all()
    out = []
    for p in rows:
        cnt = (
            await db.execute(
                select(func.count()).select_from(GeneralChecklist).where(
                    GeneralChecklist.profile_id == p.id, GeneralChecklist.is_deleted == False  # noqa: E712
                )
            )
        ).scalar() or 0
        out.append({"id": p.id, "title": p.title, "category": p.category, "created_by": p.created_by, "checklists": cnt})
    return {"items": out, "total": len(out)}


@router.post("/profiles")
async def create_profile(payload: ProfileCreate, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    p = GeneralProfile(
        id=_gid("GP"), title=payload.title[:200], category=(payload.category or "")[:60],
        created_by=getattr(user, "username", "") or "", is_deleted=False,
    )
    db.add(p)
    await db.commit()
    return {"id": p.id, "title": p.title, "category": p.category, "checklists": 0}


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    p = (await db.execute(select(GeneralProfile).where(GeneralProfile.id == profile_id))).scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    p.is_deleted = True
    await db.execute(update(GeneralChecklist).where(GeneralChecklist.profile_id == profile_id).values(is_deleted=True))
    await db.commit()
    return {"ok": True, "id": profile_id, "deleted": True}


# --- checklists -------------------------------------------------------------
@router.get("/profiles/{profile_id}/checklists")
async def list_checklists(profile_id: str, db: AsyncSession = Depends(get_db)):
    cls = (
        await db.execute(
            select(GeneralChecklist).where(
                GeneralChecklist.profile_id == profile_id, GeneralChecklist.is_deleted == False  # noqa: E712
            ).order_by(GeneralChecklist.created_at)
        )
    ).scalars().all()
    out = []
    for c in cls:
        items = (
            await db.execute(
                select(GeneralChecklistItem).where(
                    GeneralChecklistItem.checklist_id == c.id, GeneralChecklistItem.is_deleted == False  # noqa: E712
                ).order_by(GeneralChecklistItem.sort_order, GeneralChecklistItem.created_at)
            )
        ).scalars().all()
        out.append({"id": c.id, "title": c.title, "items": [
            {"id": i.id, "text": i.text, "is_done": bool(i.is_done)} for i in items
        ]})
    return {"profile_id": profile_id, "checklists": out}


class ChecklistCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@router.post("/profiles/{profile_id}/checklists")
async def create_checklist(profile_id: str, payload: ChecklistCreate, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    c = GeneralChecklist(id=_gid("GC"), profile_id=profile_id, title=payload.title[:200], is_deleted=False)
    db.add(c)
    await db.commit()
    return {"id": c.id, "title": c.title, "items": []}


@router.delete("/checklists/{checklist_id}")
async def delete_checklist(checklist_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    c = (await db.execute(select(GeneralChecklist).where(GeneralChecklist.id == checklist_id))).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="Checklist not found")
    c.is_deleted = True
    await db.execute(update(GeneralChecklistItem).where(GeneralChecklistItem.checklist_id == checklist_id).values(is_deleted=True))
    await db.commit()
    return {"ok": True, "id": checklist_id, "deleted": True}


# --- items ------------------------------------------------------------------
class ItemCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.post("/checklists/{checklist_id}/items")
async def create_item(checklist_id: str, payload: ItemCreate, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    n = (
        await db.execute(select(func.count()).select_from(GeneralChecklistItem).where(GeneralChecklistItem.checklist_id == checklist_id))
    ).scalar() or 0
    it = GeneralChecklistItem(id=_gid("GI"), checklist_id=checklist_id, text=payload.text, is_done=False, sort_order=n, is_deleted=False)
    db.add(it)
    await db.commit()
    return {"id": it.id, "text": it.text, "is_done": False}


class ItemUpdate(BaseModel):
    is_done: Optional[bool] = None
    text: Optional[str] = None


@router.patch("/items/{item_id}")
async def update_item(item_id: str, payload: ItemUpdate, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    it = (await db.execute(select(GeneralChecklistItem).where(GeneralChecklistItem.id == item_id))).scalar_one_or_none()
    if it is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if payload.is_done is not None:
        it.is_done = payload.is_done
    if payload.text is not None:
        it.text = payload.text
    await db.commit()
    return {"id": it.id, "text": it.text, "is_done": bool(it.is_done)}


@router.delete("/items/{item_id}")
async def delete_item(item_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    it = (await db.execute(select(GeneralChecklistItem).where(GeneralChecklistItem.id == item_id))).scalar_one_or_none()
    if it is None:
        raise HTTPException(status_code=404, detail="Item not found")
    it.is_deleted = True
    await db.commit()
    return {"ok": True, "id": item_id, "deleted": True}
