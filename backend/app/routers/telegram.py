"""Telegram integration API.

* ``POST /api/telegram/webhook`` is **public** (Telegram calls it) but protected
  by the ``X-Telegram-Bot-Api-Secret-Token`` header when
  ``TELEGRAM_WEBHOOK_SECRET`` is configured.
* Everything else (status, prefs, test, webhook management) is admin-only.

The webhook always returns HTTP 200 so Telegram never retries (which would flood
the bot); failures are logged instead.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_db
from pydantic import BaseModel

from app.config import settings
from app.routers.auth import require_admin, get_current_active_user
from app.services import telegram as tg
from app.services.audit import record_audit

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["telegram"])


class PrefsUpdate(BaseModel):
    events: Optional[Dict[str, bool]] = None
    sound: Optional[Dict[str, bool]] = None
    channels: Optional[Dict[str, Dict[str, Any]]] = None
    min_priority: Optional[str] = None
    include_buttons: Optional[bool] = None
    app_base_url: Optional[str] = None
    allowed_chat_ids: Optional[List[str]] = None


class WebhookRequest(BaseModel):
    webhook_url: str


# ── Public webhook (Telegram → us) ──────────────────────────────────────────
@router.post("/webhook")
async def telegram_webhook(request: Request):
    secret = (getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None) or "").strip()
    if secret:
        sent = request.headers.get("x-telegram-bot-api-secret-token", "")
        if sent != secret:
            logger.warning("telegram webhook: bad secret token")
            return {"ok": True, "ignored": True}
    try:
        body = await request.json()
    except Exception as exc:
        logger.warning("telegram webhook: invalid JSON: %s", exc)
        return {"ok": True}
    try:
        return await tg.telegram_service.handle_update(body)
    except Exception as exc:  # never let Telegram retry-storm us
        logger.exception("telegram webhook handler crashed: %s", exc)
        return {"ok": True, "handler_error": str(exc)[:200]}


# ── Admin: status & preferences ─────────────────────────────────────────────
@router.get("/status")
async def get_status(_: object = Depends(get_current_active_user)):
    return tg.telegram_service.get_status()


@router.put("/prefs")
async def update_prefs(
    payload: PrefsUpdate,
    request: Request,
    actor=Depends(require_admin),
    db=Depends(get_db),
):
    partial: Dict[str, Any] = {}
    if payload.events is not None:
        partial["events"] = payload.events
    if payload.sound is not None:
        partial["sound"] = payload.sound
    if payload.channels is not None:
        partial["channels"] = payload.channels
    if payload.min_priority is not None:
        if payload.min_priority not in tg.PRIORITY_RANK:
            raise HTTPException(status_code=400, detail="min_priority نامعتبر است")
        partial["min_priority"] = payload.min_priority
    if payload.include_buttons is not None:
        partial["include_buttons"] = payload.include_buttons
    if payload.app_base_url is not None:
        partial["app_base_url"] = payload.app_base_url.strip()
    if payload.allowed_chat_ids is not None:
        partial["allowed_chat_ids"] = [str(c).strip() for c in payload.allowed_chat_ids if str(c).strip()]

    # Persist through the request's session; a failed write is now a real
    # error (500), not a silent success that reverts on restart.
    updated = await tg.update_prefs(partial, db=db)
    await record_audit(
        action="update", entity_type="telegram_prefs", entity_id="prefs",
        detail=f"Updated Telegram prefs: {sorted(partial.keys())}", user=actor, request=request,
    )
    return {"ok": True, "prefs": updated}


@router.post("/test")
async def test_send(actor=Depends(require_admin)):
    results = await tg.telegram_service.test_send()
    return {"ok": any(r.get("ok") for r in results), "results": results}


# ── Admin: webhook management ───────────────────────────────────────────────
@router.get("/webhook-info")
async def webhook_info(_: object = Depends(require_admin)):
    return await tg.telegram_service.webhook_info()


@router.post("/set-webhook")
async def set_webhook(payload: WebhookRequest, _: object = Depends(require_admin)):
    return await tg.telegram_service.set_webhook(payload.webhook_url.strip())


@router.post("/delete-webhook")
async def delete_webhook(_: object = Depends(require_admin)):
    return await tg.telegram_service.delete_webhook()
