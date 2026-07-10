"""Editable Schedule-of-Charges tariff + the offer-letter charge calculator.

- GET  /api/charge-tariff            → all rules (auto-seeds defaults when empty)
- POST /api/charge-tariff            → create/update ONE rule (owner edits — tariffs change yearly)
- DELETE /api/charge-tariff/{id}     → soft-quarantine a rule (never hard-deleted)
- POST /api/charge-tariff/compute    → processing charges for a set of facilities
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.charge_tariff import ChargeRule
from app.routers.auth import require_editor
from app.services import charge_calc
from app.services.audit import record_audit

router = APIRouter()


def _out(r: ChargeRule) -> dict:
    return {
        "id": r.id, "segment": r.segment, "rule_key": r.rule_key, "label": r.label or "",
        "method": r.method, "rate": float(r.rate or 0),
        "min_charge": float(r.min_charge) if r.min_charge is not None else None,
        "max_charge": float(r.max_charge) if r.max_charge is not None else None,
        "small_threshold": float(r.small_threshold) if r.small_threshold is not None else None,
        "small_min_charge": float(r.small_min_charge) if r.small_min_charge is not None else None,
        "notes": r.notes or "", "version": r.version or "",
        "enabled": bool(r.enabled), "sort_order": int(r.sort_order or 0),
    }


async def _all_rules(db: AsyncSession) -> List[ChargeRule]:
    rows = (
        await db.execute(select(ChargeRule).where(ChargeRule.is_deleted == False))  # noqa: E712
    ).scalars().all()
    if not rows:
        # fill-empty-only seed from the scanned booklet — never overwrites edits
        for d in charge_calc.DEFAULT_RULES:
            db.add(ChargeRule(**{**d, "enabled": True}))
        await db.commit()
        rows = (
            await db.execute(select(ChargeRule).where(ChargeRule.is_deleted == False))  # noqa: E712
        ).scalars().all()
    return sorted(rows, key=lambda r: (r.segment or "", r.sort_order or 0))


@router.get("")
@router.get("/")
async def list_rules(db: AsyncSession = Depends(get_db), user=Depends(require_editor)):
    rows = await _all_rules(db)
    return {"rules": [_out(r) for r in rows], "rule_keys": charge_calc.RULE_KEYS}


class RuleIn(BaseModel):
    id: str = ""                      # empty → new rule
    segment: str = Field(pattern="^(corporate|individual)$")
    rule_key: str
    label: str = ""
    method: str = Field(pattern="^(per_mille|percent|flat)$")
    rate: float = 0
    min_charge: Optional[float] = None
    max_charge: Optional[float] = None
    small_threshold: Optional[float] = None
    small_min_charge: Optional[float] = None
    notes: str = ""
    version: str = ""
    enabled: bool = True
    sort_order: int = 0


@router.post("")
@router.post("/")
async def upsert_rule(
    payload: RuleIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    if payload.rule_key not in charge_calc.RULE_KEYS:
        raise HTTPException(status_code=422, detail=f"rule_key نامعتبر — یکی از {charge_calc.RULE_KEYS}")
    r = None
    if payload.id.strip():
        r = (
            await db.execute(select(ChargeRule).where(ChargeRule.id == payload.id.strip()))
        ).scalar_one_or_none()
    created = r is None
    if r is None:
        import uuid

        r = ChargeRule(id=f"CR-{payload.segment[:4]}-{uuid.uuid4().hex[:8]}")
        db.add(r)
    for k in ("segment", "rule_key", "label", "method", "rate", "min_charge", "max_charge",
              "small_threshold", "small_min_charge", "notes", "version", "enabled", "sort_order"):
        setattr(r, k, getattr(payload, k))
    r.is_deleted = False
    await db.commit()
    await record_audit(
        action="create" if created else "update", entity_type="charge_rule", entity_id=r.id,
        detail=f"تعرفهٔ شارژ «{r.label or r.rule_key}» ({r.segment}) {'ایجاد' if created else 'به‌روزرسانی'} شد",
        user=user, request=request, db=db,
    )
    return {"ok": True, "created": created, "rule": _out(r)}


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    r = (await db.execute(select(ChargeRule).where(ChargeRule.id == rule_id))).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="قاعده یافت نشد")
    r.is_deleted = True   # quarantine, not delete
    await db.commit()
    await record_audit(
        action="delete", entity_type="charge_rule", entity_id=r.id,
        detail=f"تعرفهٔ شارژ «{r.label or r.rule_key}» قرنطینه شد",
        user=user, request=request, db=db,
    )
    return {"ok": True}


class ComputeItem(BaseModel):
    facility_type: str = ""
    amount: str = ""                  # free text — "2,800,000/-" accepted
    covered_by_fd: bool = False
    staff_facility: bool = False
    temporary: bool = False


class ComputeIn(BaseModel):
    segment: str = "corporate"
    items: List[ComputeItem] = []


@router.post("/compute")
async def compute(
    payload: ComputeIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor),
):
    rows = await _all_rules(db)
    result = charge_calc.compute_charges(
        [_out(r) for r in rows],
        [i.model_dump() for i in payload.items],
        segment=payload.segment,
    )
    return {"ok": True, **result}
