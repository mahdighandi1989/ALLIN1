"""Staff directory (bank employees) — wired at /api/staff.

Everyone signed-in can view + search; editors can add / edit / delete (people move
departments or leave, so every field is editable). Names carry an editable Persian
equivalent (``name_fa``). ``region`` separates the Persian-Gulf (UAE) list from any
Iran-side list added later.
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.staff import StaffMember, generate_staff_id
from app.routers.auth import require_editor, get_current_active_user
from app.services.audit import record_audit

router = APIRouter(tags=["staff"], dependencies=[Depends(get_current_active_user)])


class StaffOut(BaseModel):
    id: str
    name: str
    name_fa: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    telephone: Optional[str] = None
    ext: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    region: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class StaffListResponse(BaseModel):
    items: List[StaffOut]
    total: int


class StaffCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    name_fa: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=200)
    title: Optional[str] = Field(default=None, max_length=150)
    telephone: Optional[str] = Field(default=None, max_length=60)
    ext: Optional[str] = Field(default=None, max_length=20)
    fax: Optional[str] = Field(default=None, max_length=60)
    email: Optional[str] = Field(default=None, max_length=150)
    mobile: Optional[str] = Field(default=None, max_length=60)
    region: Optional[str] = Field(default="Persian Gulf", max_length=80)
    notes: Optional[str] = None


class StaffUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    name_fa: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=200)
    title: Optional[str] = Field(default=None, max_length=150)
    telephone: Optional[str] = Field(default=None, max_length=60)
    ext: Optional[str] = Field(default=None, max_length=20)
    fax: Optional[str] = Field(default=None, max_length=60)
    email: Optional[str] = Field(default=None, max_length=150)
    mobile: Optional[str] = Field(default=None, max_length=60)
    region: Optional[str] = Field(default=None, max_length=80)
    notes: Optional[str] = None


@router.get("/", response_model=StaffListResponse)
async def list_staff(
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = Query(None, description="Search name / Persian name / dept / email / ext"),
    region: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
):
    base = select(StaffMember).where(StaffMember.is_deleted == False)  # noqa: E712
    if region:
        base = base.where(StaffMember.region == region)
    if department:
        base = base.where(StaffMember.department == department)
    if q:
        like = f"%{q.strip()}%"
        base = base.where(or_(
            StaffMember.name.ilike(like), StaffMember.name_fa.ilike(like),
            StaffMember.department.ilike(like), StaffMember.email.ilike(like),
            StaffMember.ext.ilike(like), StaffMember.telephone.ilike(like),
            StaffMember.title.ilike(like),
        ))
    rows = (await db.execute(base.order_by(StaffMember.name).limit(2000))).scalars().all()
    return StaffListResponse(items=rows, total=len(rows))


@router.get("/departments", response_model=List[str])
async def list_departments(db: AsyncSession = Depends(get_db), region: Optional[str] = Query(None)):
    base = select(StaffMember.department).where(
        StaffMember.is_deleted == False,  # noqa: E712
        StaffMember.department.isnot(None), StaffMember.department != "",
    )
    if region:
        base = base.where(StaffMember.region == region)
    rows = (await db.execute(base.distinct())).scalars().all()
    return sorted({(d or "").strip() for d in rows if (d or "").strip()})


@router.post("/", response_model=StaffOut, status_code=201)
async def create_staff(
    payload: StaffCreate, request: Request,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    s = StaffMember(id=generate_staff_id(), **payload.model_dump(exclude_none=True))
    s.updated_by = getattr(user, "username", "") or ""
    db.add(s)
    await db.commit()
    await db.refresh(s)
    await record_audit(action="create", entity_type="staff", entity_id=s.id,
                       detail=f"افزودنِ کارمند «{s.name}»" + (f" — {s.department}" if s.department else ""),
                       user=user, request=request, db=db)
    return s


@router.patch("/{staff_id}", response_model=StaffOut)
async def update_staff(
    staff_id: str, payload: StaffUpdate, request: Request,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    s = (await db.execute(select(StaffMember).where(
        StaffMember.id == staff_id, StaffMember.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if s is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(s, k, v)
    s.updated_by = getattr(user, "username", "") or ""
    await db.commit()
    await db.refresh(s)
    await record_audit(action="update", entity_type="staff", entity_id=s.id,
                       detail=f"ویرایشِ کارمند «{s.name}»", user=user, request=request, db=db)
    return s


@router.delete("/{staff_id}", status_code=204)
async def delete_staff(
    staff_id: str, request: Request,
    db: AsyncSession = Depends(get_db), user=Depends(require_editor),
):
    s = (await db.execute(select(StaffMember).where(
        StaffMember.id == staff_id, StaffMember.is_deleted == False))).scalar_one_or_none()  # noqa: E712
    if s is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    s.is_deleted = True
    await db.commit()
    await record_audit(action="delete", entity_type="staff", entity_id=s.id,
                       detail=f"حذفِ کارمند «{s.name}»", user=user, request=request, db=db)
    return None
