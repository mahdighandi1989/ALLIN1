"""System settings: editable key/values (DB) + read-only runtime config view."""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.config import settings as app_settings
from app.models.system_setting import SystemSetting, EDITABLE_SETTINGS
from app.routers.auth import require_admin, get_current_active_user
from app.services.audit import record_audit

router = APIRouter(tags=["settings"])


class SettingsUpdate(BaseModel):
    values: Dict[str, str]


async def _load_editable(db: AsyncSession) -> Dict[str, str]:
    rows = (await db.execute(select(SystemSetting))).scalars().all()
    stored = {r.key: r.value for r in rows}
    out = {}
    for key, meta in EDITABLE_SETTINGS.items():
        out[key] = stored.get(key, meta["default"])
    return out


@router.get("/")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    """Return editable settings (with metadata) and a read-only runtime config view."""
    editable_values = await _load_editable(db)
    editable = [
        {
            "key": key,
            "value": editable_values[key],
            "label": meta["label"],
            "type": meta["type"],
        }
        for key, meta in EDITABLE_SETTINGS.items()
    ]
    # Read-only operational config (sourced from env). Never expose secrets.
    runtime = {
        "environment": app_settings.ENVIRONMENT,
        "auth_disabled": bool(getattr(app_settings, "AUTH_DISABLED", False)),
        "login_rate_limit_per_minute": app_settings.LOGIN_RATE_LIMIT_PER_MINUTE,
        "account_lockout_threshold": app_settings.ACCOUNT_LOCKOUT_THRESHOLD,
        "account_lockout_minutes": app_settings.ACCOUNT_LOCKOUT_MINUTES,
        "access_token_expire_minutes": app_settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "app_version": app_settings.APP_VERSION,
    }
    return {"editable": editable, "runtime": runtime}


@router.put("/")
async def update_settings(
    payload: SettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    """Update editable settings (admin only). Unknown keys are rejected."""
    unknown = [k for k in payload.values if k not in EDITABLE_SETTINGS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown settings: {unknown}")

    # Light type validation for numeric settings.
    for key, value in payload.values.items():
        if EDITABLE_SETTINGS[key]["type"] == "number":
            try:
                int(value)
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail=f"'{key}' must be a number")

    for key, value in payload.values.items():
        existing = (
            await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        ).scalar_one_or_none()
        if existing:
            existing.value = str(value)
        else:
            db.add(SystemSetting(key=key, value=str(value)))

    await db.commit()
    await record_audit(
        action="update", entity_type="settings",
        entity_id=",".join(sorted(payload.values.keys()))[:64],
        detail=f"Updated settings: {sorted(payload.values.keys())}",
        user=actor, request=request, db=db,
    )
    return {"editable": [
        {"key": k, "value": v, "label": EDITABLE_SETTINGS[k]["label"], "type": EDITABLE_SETTINGS[k]["type"]}
        for k, v in (await _load_editable(db)).items()
    ]}
