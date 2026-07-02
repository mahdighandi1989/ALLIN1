"""Admin database-cleanup (de-dup) API — REVIEW FIRST.

  POST /api/cleanup/scan     → dry-run report (changes nothing)
  POST /api/cleanup/apply    → soft-delete the duplicates (reversible), logged per customer
  GET  /api/cleanup/history  → recent runs
  GET  /api/cleanup/config   → schedule + AI settings + available models
  PUT  /api/cleanup/config   → update schedule / AI second-opinion
  POST /api/cleanup/ai-review→ optional AI «second opinion» (best-effort)
"""
import json

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.cleanup_run import CleanupRun
from app.models.system_setting import SystemSetting
from app.routers.auth import require_admin
from app.services import db_cleanup
from app.services.audit import record_audit

router = APIRouter(prefix="/api/cleanup", tags=["cleanup"])

_SCHEDULES = {"off", "daily", "weekly", "monthly"}


async def _get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    row = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    return (row.value if row and row.value is not None else default)


async def _set_setting(db: AsyncSession, key: str, value: str) -> None:
    row = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
    if row:
        row.value = str(value)
    else:
        db.add(SystemSetting(key=key, value=str(value)))


async def _save_run(db: AsyncSession, kind: str, trigger: str, username: str, counts: dict, detail: str = "") -> None:
    db.add(CleanupRun(kind=kind, trigger=trigger, username=username,
                      counts_json=json.dumps(counts, ensure_ascii=False), detail=detail))


@router.post("/scan")
async def scan(request: Request, db: AsyncSession = Depends(get_db), actor=Depends(require_admin)):
    """Full de-dup report. Nothing is changed."""
    report = await db_cleanup.scan(db)
    await _save_run(db, "scan", "manual", getattr(actor, "username", "?"), report["counts"])
    await db.commit()
    return report


class ApplyBody(BaseModel):
    only: list[str] | None = None          # limit to specific entity keys, or None = all
    confirm_ids: list[str] | None = None   # 'probable' removals the admin/AI confirmed


@router.post("/apply")
async def apply(body: ApplyBody, request: Request, db: AsyncSession = Depends(get_db), actor=Depends(require_admin)):
    """Soft-delete duplicate records (reversible via Recycle Bin), logging each
    removal under its customer's Logs tab. Re-scans first so it applies exactly the
    current result. Only 'certain' duplicates are removed unless a 'probable' row's
    id is passed in ``confirm_ids`` (confirmed by a human or the AI adjudicator)."""
    result = await db_cleanup.apply(db, actor, only=body.only, confirm_ids=body.confirm_ids)
    await _save_run(db, "apply", "manual", getattr(actor, "username", "?"), result["removed"],
                    detail=f"حذفِ {result['removed'].get('total', 0)} رکوردِ تکراری")
    await record_audit(action="delete", entity_type="cleanup", entity_id="apply",
                       detail=f"پاک‌سازیِ دیتابیس: {result['removed']}", user=actor, request=request, db=db)
    await db.commit()
    return result


@router.get("/history")
async def history(db: AsyncSession = Depends(get_db), actor=Depends(require_admin), limit: int = 30):
    rows = (await db.execute(select(CleanupRun).order_by(desc(CleanupRun.created_at)).limit(min(limit, 100)))).scalars().all()
    return {"runs": [{
        "id": r.id, "kind": r.kind, "trigger": r.trigger, "username": r.username,
        "counts": json.loads(r.counts_json) if r.counts_json else {},
        "detail": r.detail, "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]}


@router.get("/config")
async def get_config(db: AsyncSession = Depends(get_db), actor=Depends(require_admin)):
    """Schedule + AI second-opinion config, plus the available AI models (best first)
    so an admin can see/choose which model powers the second opinion."""
    from app.ai import ai_manager
    models, active = [], None
    try:
        # list enabled+configured models by priority (best first)
        caps = await ai_manager.capable_models(db, "documents")
        for m in caps:
            models.append({"id": m["id"], "name": m["display_name"], "provider": m.get("provider_key"), "priority": m.get("priority")})
        resolved = await ai_manager.resolve(db, "data_validation")
        active = resolved.display_name if resolved else None
    except Exception:
        pass
    return {
        "schedule": await _get_setting(db, "cleanup_schedule", "off"),
        "ai_review": await _get_setting(db, "cleanup_ai_review", "off"),
        "last_run": await _get_setting(db, "cleanup_last_run", ""),
        "schedules": sorted(_SCHEDULES),
        "models": models,
        "active_model": active,
        "ai_available": active is not None,
    }


class ConfigBody(BaseModel):
    schedule: str | None = None
    ai_review: str | None = None


@router.put("/config")
async def put_config(body: ConfigBody, request: Request, db: AsyncSession = Depends(get_db), actor=Depends(require_admin)):
    if body.schedule is not None:
        sched = body.schedule if body.schedule in _SCHEDULES else "off"
        await _set_setting(db, "cleanup_schedule", sched)
    if body.ai_review is not None:
        await _set_setting(db, "cleanup_ai_review", "on" if body.ai_review == "on" else "off")
    await record_audit(action="update", entity_type="settings", entity_id="cleanup",
                       detail=f"تنظیماتِ پاک‌سازی: schedule={body.schedule}, ai={body.ai_review}",
                       user=actor, request=request, db=db)
    await db.commit()
    return await get_config(db, actor)


@router.post("/ai-review")
async def ai_review(request: Request, db: AsyncSession = Depends(get_db), actor=Depends(require_admin)):
    """AI adjudication of the ambiguous 'probable' groups: for each, the active
    model decides (seeing every field) whether a candidate is the SAME record whose
    data was updated over time, or a genuinely distinct record. Best-effort —
    returns ``{available:false}`` with no model/network. Nothing is auto-deleted;
    confirmed ids are returned for a one-click apply."""
    result = await db_cleanup.ai_adjudicate(db)
    await _save_run(db, "ai_review", "manual", getattr(actor, "username", "?"),
                    {"available": result.get("available"), "calls": result.get("calls", 0),
                     "confirmed": len(result.get("confirmed_ids") or [])},
                    detail="داوریِ هوش مصنوعیِ مواردِ نیازمندِ بررسی")
    await db.commit()
    return result
