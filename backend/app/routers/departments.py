"""Recipient departments + managers — wired at /api/departments.

Everyone signed-in can view/search (for the letter's searchable «گیرنده» fields);
editors can resolve (find-or-create + manager rotation) and edit. ``resolve`` is
the smart entry point used when a letter is saved: it matches an existing
department by a normalized key (and a fuzzy fallback so a tiny spelling
difference doesn't spawn a duplicate), creates it if new, and — when the manager
changed — moves the old manager into the ordered ``previous_managers`` history.
"""
import json
import re
from datetime import date
from difflib import SequenceMatcher
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.department import Department, generate_dept_id
from app.routers.auth import require_editor, get_current_active_user
from app.services.audit import record_audit

router = APIRouter(tags=["departments"], dependencies=[Depends(get_current_active_user)])

_FUZZY_THRESHOLD = 0.88


def _norm(s: str) -> str:
    """Normalize a department/manager name for de-duplication."""
    s = (s or "").strip().lower()
    # unify Arabic/Persian variants and strip ZWNJ / diacritics
    s = s.translate({0x064A: 0x06CC, 0x0643: 0x06A9, 0x0629: 0x0647, 0x200C: 0x20, 0x200F: None, 0x200E: None})
    s = re.sub(r"[ً-ْ]", "", s)        # Arabic harakat
    s = re.sub(r"[^\w؀-ۿ]+", " ", s)    # punctuation → space
    s = re.sub(r"\s+", " ", s).strip()
    return s


async def _find_match(db: AsyncSession, name: str) -> Optional[Department]:
    """Find an existing department by exact-normalized then fuzzy name."""
    norm = _norm(name)
    if not norm:
        return None
    rows = (await db.execute(select(Department).where(Department.is_deleted == False))).scalars().all()  # noqa: E712
    for d in rows:
        if (d.name_norm or _norm(d.name)) == norm:
            return d
    best, best_d = 0.0, None
    for d in rows:
        r = SequenceMatcher(None, norm, d.name_norm or _norm(d.name)).ratio()
        if r > best:
            best, best_d = r, d
    return best_d if best >= _FUZZY_THRESHOLD else None


def _prev_list(d: Department) -> list:
    try:
        v = json.loads(d.previous_managers) if d.previous_managers else []
        return v if isinstance(v, list) else []
    except Exception:
        return []


class DeptOut(BaseModel):
    id: str
    name: str
    name_fa: Optional[str] = None
    current_manager: Optional[str] = None
    current_manager_fa: Optional[str] = None
    manager_title: Optional[str] = None
    previous_managers: Optional[list] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


def _out(d: Department) -> DeptOut:
    return DeptOut(
        id=d.id, name=d.name, name_fa=d.name_fa, current_manager=d.current_manager,
        current_manager_fa=d.current_manager_fa, manager_title=d.manager_title,
        previous_managers=_prev_list(d), notes=d.notes,
    )


@router.get("/", response_model=List[DeptOut])
async def list_departments(db: AsyncSession = Depends(get_db), q: Optional[str] = Query(None)):
    base = select(Department).where(Department.is_deleted == False)  # noqa: E712
    if q:
        like = f"%{q.strip()}%"
        base = base.where(or_(Department.name.ilike(like), Department.name_fa.ilike(like), Department.current_manager.ilike(like)))
    rows = (await db.execute(base.order_by(Department.name).limit(1000))).scalars().all()
    return [_out(d) for d in rows]


class DeptResolve(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    name_fa: Optional[str] = Field(default=None, max_length=200)
    manager: Optional[str] = Field(default=None, max_length=200)
    manager_fa: Optional[str] = Field(default=None, max_length=200)
    manager_title: Optional[str] = Field(default=None, max_length=120)


@router.post("/resolve", response_model=DeptOut)
async def resolve_department(payload: DeptResolve, request: Request, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    """Find-or-create the department; rotate the manager into history if it changed."""
    uname = getattr(user, "username", "") or ""
    d = await _find_match(db, payload.name)
    created = d is None
    if d is None:
        d = Department(id=generate_dept_id(), name=payload.name.strip()[:200], name_norm=_norm(payload.name))
        db.add(d)
    if payload.name_fa and not d.name_fa:
        d.name_fa = payload.name_fa.strip()[:200]
    if payload.manager_title:
        d.manager_title = payload.manager_title.strip()[:120]

    new_mgr = (payload.manager or "").strip()
    rotated = False
    if new_mgr and _norm(new_mgr) != _norm(d.current_manager or ""):
        if (d.current_manager or "").strip():
            prev = _prev_list(d)
            prev.append({"name": d.current_manager, "name_fa": d.current_manager_fa, "until": date.today().isoformat()})
            d.previous_managers = json.dumps(prev, ensure_ascii=False)
            rotated = True
        d.current_manager = new_mgr[:200]
        d.current_manager_fa = (payload.manager_fa or "").strip()[:200] or None
    elif new_mgr and payload.manager_fa and not d.current_manager_fa:
        d.current_manager_fa = payload.manager_fa.strip()[:200]
    d.updated_by = uname
    await db.commit()
    await db.refresh(d)
    await record_audit(action="create" if created else "update", entity_type="department", entity_id=d.id,
                       detail=f"{'ایجادِ' if created else ('چرخشِ مدیرِ' if rotated else 'به‌روزرسانیِ')} ادارهٔ «{d.name}»"
                              + (f" → {d.current_manager}" if d.current_manager else ""),
                       user=user, request=request, db=db)
    return _out(d)


class DeptUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    name_fa: Optional[str] = Field(default=None, max_length=200)
    current_manager: Optional[str] = Field(default=None, max_length=200)
    current_manager_fa: Optional[str] = Field(default=None, max_length=200)
    manager_title: Optional[str] = Field(default=None, max_length=120)
    notes: Optional[str] = None


@router.patch("/{dept_id}", response_model=DeptOut)
async def update_department(dept_id: str, payload: DeptUpdate, request: Request, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    d = (await db.execute(select(Department).where(Department.id == dept_id, Department.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if d is None:
        raise HTTPException(status_code=404, detail="Department not found")
    data = payload.model_dump(exclude_unset=True)
    # manager change → rotate history
    if "current_manager" in data and (data["current_manager"] or "").strip() and _norm(data["current_manager"]) != _norm(d.current_manager or ""):
        if (d.current_manager or "").strip():
            prev = _prev_list(d)
            prev.append({"name": d.current_manager, "name_fa": d.current_manager_fa, "until": date.today().isoformat()})
            d.previous_managers = json.dumps(prev, ensure_ascii=False)
    for k, v in data.items():
        setattr(d, k, v)
    if "name" in data:
        d.name_norm = _norm(d.name)
    d.updated_by = getattr(user, "username", "") or ""
    await db.commit()
    await db.refresh(d)
    await record_audit(action="update", entity_type="department", entity_id=d.id,
                       detail=f"ویرایشِ ادارهٔ «{d.name}»", user=user, request=request, db=db)
    return _out(d)


@router.delete("/{dept_id}", status_code=204)
async def delete_department(dept_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    d = (await db.execute(select(Department).where(Department.id == dept_id, Department.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if d is None:
        raise HTTPException(status_code=404, detail="Department not found")
    d.is_deleted = True
    await db.commit()
    await record_audit(action="delete", entity_type="department", entity_id=d.id,
                       detail=f"حذفِ ادارهٔ «{d.name}»", user=user, request=request, db=db)
    return None
