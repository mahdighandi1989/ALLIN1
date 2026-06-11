"""Two-way Telegram integration for the banking operations panel.

This module is the single home for everything Telegram:

* **Outbound** — :class:`TelegramService` turns domain events ("a facility is
  about to expire", "a backup failed", "an offer letter was created") into
  Telegram messages, honouring per-event user preferences: which events are
  sent at all, which ring (sound) vs arrive silently, and a global minimum
  priority. Email is also supported as a secondary channel.

* **Inbound** — the same service handles Telegram ``webhook`` updates: a
  persistent reply-keyboard menu, slash commands (``/status``, ``/stats``,
  ``/expiring``, ``/fx``, ``/scan``, ``/backup``, ``/ai`` …) and a free-text
  bridge to the panel's configured AI models, so the operator can both *see*
  system state and *drive* a few actions from their phone.

Preferences live in the DB (``system_settings`` row ``telegram_prefs``) so they
survive restarts, and are mirrored into an in-memory cache so the synchronous
critical-event path (:mod:`app.services.notifications`) can read them without a
DB round-trip. Access is restricted to an allow-list of chat ids (env
``TELEGRAM_CHAT_ID`` — comma separated — plus any added from the panel), and the
webhook can additionally be protected with Telegram's ``secret_token`` header.

Everything is best-effort: when the bot token / chat id is unconfigured every
send is a graceful no-op (logged, never raised), so the rest of the app keeps
working unchanged.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TG_API = "https://api.telegram.org/bot{token}/{method}"
_TIMEOUT = 20.0

# Priority ranking for the global ``min_priority`` filter.
PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


# ---------------------------------------------------------------------------
# Event registry — the single source of truth for every notification type the
# panel can emit. Each entry drives both the default preferences and the
# settings UI (label / help / icon). Adding an event here makes it appear in the
# panel automatically and gives it a sensible default.
# ---------------------------------------------------------------------------
EVENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── Facility / KYC expiry (the headline banking alert) ──────────────
    "facility_expiring": {
        "label": "🏦 تسهیلات رو به انقضا",
        "help": "وقتی تسهیلاتی در بازهٔ هشدار به انقضا نزدیک می‌شود",
        "default_enabled": True,
        "default_sound": True,
        "icon": "🏦",
        "group": "expiry",
    },
    "facility_expired": {
        "label": "⛔️ تسهیلات منقضی‌شده",
        "help": "وقتی تاریخ انقضای تسهیلاتی گذشته است",
        "default_enabled": True,
        "default_sound": True,
        "icon": "⛔️",
        "group": "expiry",
    },
    "document_expiring": {
        "label": "📄 مدرک KYC رو به انقضا",
        "help": "انقضای نزدیک مدارک مشتری (مجوز، پاسپورت، اقامت…)",
        "default_enabled": True,
        "default_sound": False,
        "icon": "📄",
        "group": "expiry",
    },
    "expiry_scan_summary": {
        "label": "🔁 خلاصهٔ اسکن انقضا",
        "help": "خلاصهٔ نتیجهٔ اجرای اسکن انقضا (تعداد آلرت‌ها)",
        "default_enabled": True,
        "default_sound": False,
        "icon": "🔁",
        "group": "expiry",
    },
    # ── Offer letters & facilities lifecycle ────────────────────────────
    "offer_letter_created": {
        "label": "📝 نامهٔ پیشنهاد جدید",
        "help": "وقتی یک Offer Letter جدید صادر می‌شود",
        "default_enabled": True,
        "default_sound": False,
        "icon": "📝",
        "group": "banking",
    },
    "facility_created": {
        "label": "➕ تسهیلات جدید ثبت شد",
        "help": "وقتی یک تسهیلات جدید برای مشتری ثبت می‌شود",
        "default_enabled": False,
        "default_sound": False,
        "icon": "➕",
        "group": "banking",
    },
    "fx_updated": {
        "label": "💱 به‌روزرسانی نرخ ارز",
        "help": "وقتی نرخ‌های ارز تغییر می‌کنند",
        "default_enabled": False,
        "default_sound": False,
        "icon": "💱",
        "group": "banking",
    },
    # ── Data import / backup / sync ─────────────────────────────────────
    "import_done": {
        "label": "📥 ورود داده کامل شد",
        "help": "وقتی ایمپورت اکسل با موفقیت تمام می‌شود",
        "default_enabled": True,
        "default_sound": False,
        "icon": "📥",
        "group": "data",
    },
    "import_failed": {
        "label": "💥 خطا در ورود داده",
        "help": "وقتی ایمپورت اکسل با خطا متوقف می‌شود",
        "default_enabled": True,
        "default_sound": True,
        "icon": "💥",
        "group": "data",
    },
    "backup_done": {
        "label": "☁️ پشتیبان‌گیری انجام شد",
        "help": "وقتی پشتیبان‌گیری/سینک Google Drive کامل می‌شود",
        "default_enabled": False,
        "default_sound": False,
        "icon": "☁️",
        "group": "data",
    },
    "backup_failed": {
        "label": "🛑 خطا در پشتیبان‌گیری",
        "help": "وقتی پشتیبان‌گیری/سینک Drive شکست می‌خورد",
        "default_enabled": True,
        "default_sound": True,
        "icon": "🛑",
        "group": "data",
    },
    # ── System / health (used by the legacy critical-event path too) ────
    "scan_failed": {
        "label": "🚨 خطا در اسکن داده",
        "help": "وقتی اسکن دادهٔ سیستم با خطا مواجه می‌شود",
        "default_enabled": True,
        "default_sound": True,
        "icon": "🚨",
        "group": "system",
    },
    "verify_failed": {
        "label": "🚨 خطا در راستی‌آزمایی",
        "help": "وقتی راستی‌آزمایی دادهٔ سیستم ناموفق است",
        "default_enabled": True,
        "default_sound": True,
        "icon": "🚨",
        "group": "system",
    },
    "task_failed": {
        "label": "🚨 خطا در وظیفهٔ پس‌زمینه",
        "help": "وقتی یک کار پس‌زمینه ناموفق می‌شود",
        "default_enabled": True,
        "default_sound": True,
        "icon": "🚨",
        "group": "system",
    },
    "security_alert": {
        "label": "🔐 هشدار امنیتی",
        "help": "رویدادهای امنیتی مهم (مثل تلاش‌های ورود مشکوک)",
        "default_enabled": True,
        "default_sound": True,
        "icon": "🔐",
        "group": "system",
    },
    "daily_report": {
        "label": "📊 گزارش روزانهٔ سیستم",
        "help": "گزارش دوره‌ای از وضعیت پرتفوی و انقضاها",
        "default_enabled": False,
        "default_sound": False,
        "icon": "📊",
        "group": "system",
    },
    "manual_test": {
        "label": "🧪 پیام تست دستی",
        "help": "برای دکمهٔ «ارسال تست» در پنل",
        "default_enabled": True,
        "default_sound": True,
        "icon": "🧪",
        "group": "system",
    },
}

# Grouping for the settings UI (title shown above each block).
EVENT_GROUPS: List[Dict[str, Any]] = [
    {"id": "expiry", "title": "انقضا (تسهیلات و مدارک)", "icon": "🏦"},
    {"id": "banking", "title": "عملیات بانکی", "icon": "💼"},
    {"id": "data", "title": "ورود داده، پشتیبان و سینک", "icon": "📥"},
    {"id": "system", "title": "سیستم و سلامت", "icon": "🛡"},
]


# ---------------------------------------------------------------------------
# Persistent reply keyboard (the fixed menu under the input box) + text aliases.
# Tapping a button sends its text; the alias map turns that text into a command.
# ---------------------------------------------------------------------------
PERSISTENT_REPLY_KEYBOARD: Dict[str, Any] = {
    "keyboard": [
        [{"text": "📊 وضعیت"}, {"text": "📈 آمار"}],
        [{"text": "🏦 رو به انقضا"}, {"text": "💱 نرخ ارز"}],
        [{"text": "🤖 پرسش از AI"}, {"text": "🔁 اسکن انقضا"}],
        [{"text": "☁️ پشتیبان‌گیری"}, {"text": "📋 منو"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
    "input_field_placeholder": "یک دکمه بزن یا سؤالت را تایپ کن…",
}

TEXT_ALIASES: Dict[str, str] = {
    "📊 وضعیت": "/status",
    "📈 آمار": "/stats",
    "🏦 رو به انقضا": "/expiring",
    "💱 نرخ ارز": "/fx",
    "🤖 پرسش از AI": "/ai",
    "🔁 اسکن انقضا": "/scan",
    "☁️ پشتیبان‌گیری": "/backup",
    "📋 منو": "/menu",
}


# ---------------------------------------------------------------------------
# Preferences — DB-backed JSON with an in-memory cache.
# ---------------------------------------------------------------------------
_PREFS_KEY = "telegram_prefs"
_PREFS_CACHE: Optional[Dict[str, Any]] = None


def build_default_prefs() -> Dict[str, Any]:
    return {
        "events": {k: v["default_enabled"] for k, v in EVENT_REGISTRY.items()},
        "sound": {k: v["default_sound"] for k, v in EVENT_REGISTRY.items()},
        "channels": {
            "telegram": {"enabled": True},
            "email": {"enabled": False},
        },
        "min_priority": "low",
        "include_buttons": True,
        # Where deep-link buttons point (e.g. https://banking.example.com).
        "app_base_url": "",
        # Extra chat ids allowed to control the bot (env TELEGRAM_CHAT_ID is
        # always allowed too). Strings.
        "allowed_chat_ids": [],
    }


def _merge_into_defaults(stored: Dict[str, Any]) -> Dict[str, Any]:
    """Deep-merge a stored prefs blob over the freshly-built defaults, so new
    events/keys appear automatically without losing the user's choices."""
    prefs = build_default_prefs()
    for k, v in (stored or {}).items():
        if isinstance(v, dict) and isinstance(prefs.get(k), dict):
            prefs[k].update(v)
        else:
            prefs[k] = v
    # Backfill any event added to the registry after prefs were first saved.
    for ev, meta in EVENT_REGISTRY.items():
        prefs["events"].setdefault(ev, meta["default_enabled"])
        prefs["sound"].setdefault(ev, meta["default_sound"])
    return prefs


def get_prefs() -> Dict[str, Any]:
    """Synchronous, cache-only read (defaults until :func:`load_prefs` runs)."""
    return _PREFS_CACHE if _PREFS_CACHE is not None else build_default_prefs()


async def load_prefs(db=None) -> Dict[str, Any]:
    """Load prefs from the DB into the cache. Safe to call at startup."""
    global _PREFS_CACHE
    stored: Dict[str, Any] = {}
    try:
        from sqlalchemy import select
        from app.models.system_setting import SystemSetting
        from app.database import AsyncSessionLocal

        async def _read(session) -> None:
            nonlocal stored
            row = (
                await session.execute(
                    select(SystemSetting).where(SystemSetting.key == _PREFS_KEY)
                )
            ).scalar_one_or_none()
            if row and row.value:
                try:
                    stored = json.loads(row.value)
                except (TypeError, ValueError):
                    stored = {}

        if db is not None:
            await _read(db)
        else:
            async with AsyncSessionLocal() as session:
                await _read(session)
    except Exception as exc:  # pragma: no cover - DB optional at import time
        logger.warning("telegram: load prefs failed, using defaults: %s", exc)
    _PREFS_CACHE = _merge_into_defaults(stored)
    return _PREFS_CACHE


async def save_prefs(prefs: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Persist prefs to the DB and refresh the cache."""
    global _PREFS_CACHE
    _PREFS_CACHE = _merge_into_defaults(prefs)
    try:
        from sqlalchemy import select
        from app.models.system_setting import SystemSetting
        from app.database import AsyncSessionLocal

        payload = json.dumps(_PREFS_CACHE, ensure_ascii=False)

        async def _write(session) -> None:
            row = (
                await session.execute(
                    select(SystemSetting).where(SystemSetting.key == _PREFS_KEY)
                )
            ).scalar_one_or_none()
            if row:
                row.value = payload
            else:
                session.add(SystemSetting(key=_PREFS_KEY, value=payload))
            await session.commit()

        if db is not None:
            await _write(db)
        else:
            async with AsyncSessionLocal() as session:
                await _write(session)
    except Exception as exc:
        logger.warning("telegram: save prefs failed: %s", exc)
    return _PREFS_CACHE


async def update_prefs(partial: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Deep-merge a partial update over current prefs and persist."""
    cur = dict(get_prefs())
    for k, v in (partial or {}).items():
        if isinstance(v, dict) and isinstance(cur.get(k), dict):
            merged = dict(cur[k])
            merged.update(v)
            cur[k] = merged
        else:
            cur[k] = v
    return await save_prefs(cur, db=db)


# ---------------------------------------------------------------------------
# Chat allow-list + message formatting helpers
# ---------------------------------------------------------------------------
def _env_chat_ids() -> List[str]:
    raw = (getattr(settings, "TELEGRAM_CHAT_ID", None) or "").replace(",", " ")
    return [c.strip() for c in raw.split() if c.strip()]


def allowed_chat_ids() -> List[str]:
    """Union of env chat ids and panel-added chat ids (all as strings)."""
    ids = list(_env_chat_ids())
    for c in get_prefs().get("allowed_chat_ids", []) or []:
        c = str(c).strip()
        if c and c not in ids:
            ids.append(c)
    return ids


def is_allowed(chat_id: Any) -> bool:
    ids = allowed_chat_ids()
    if not ids:
        # No allow-list configured yet — bootstrap mode (see handle_update).
        return False
    return str(chat_id) in ids


def build_inline_keyboard(app_base_url: str, event: str) -> Optional[Dict[str, Any]]:
    """A context-aware deep-link button row, or None when no base URL is set."""
    base = (app_base_url or "").rstrip("/")
    if not base:
        return None
    row: List[Dict[str, str]] = []
    if event in ("facility_expiring", "facility_expired", "expiry_scan_summary", "facility_created"):
        row.append({"text": "🏦 تسهیلات", "url": f"{base}/facilities"})
    elif event == "offer_letter_created":
        row.append({"text": "📝 نامه‌های پیشنهاد", "url": f"{base}/offer-letter"})
    elif event == "fx_updated":
        row.append({"text": "💱 نرخ ارز", "url": f"{base}/settings"})
    else:
        row.append({"text": "📊 داشبورد", "url": f"{base}/dashboard"})
    return {"inline_keyboard": [row]}


# ---------------------------------------------------------------------------
# Telegram Bot API client
# ---------------------------------------------------------------------------
class TelegramChannel:
    """Thin async wrapper over the Telegram Bot API (httpx)."""

    name = "telegram"

    def __init__(self, bot_token: Optional[str], chat_id: Optional[str]):
        self.bot_token = (bot_token or "").strip() or None
        # The default *outbound* chat: first env chat id (notifications go here).
        ids = _env_chat_ids()
        self.chat_id = (chat_id or (ids[0] if ids else "")).strip() or None

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def _url(self, method: str) -> str:
        return _TG_API.format(token=self.bot_token, method=method)

    async def _post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST JSON to a Bot API method. Retries once without Markdown on a
        parse error. Never raises — returns ``{ok, ...}``."""
        if not self.bot_token:
            return {"ok": False, "error": "TELEGRAM_BOT_TOKEN unset"}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(self._url(method), json=payload)
            if resp.status_code == 200:
                return resp.json()
            body = resp.text or ""
            if "can't parse" in body.lower() and payload.get("parse_mode"):
                retry = dict(payload)
                retry.pop("parse_mode", None)
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp2 = await client.post(self._url(method), json=retry)
                if resp2.status_code == 200:
                    return resp2.json()
                return {"ok": False, "error": f"HTTP {resp2.status_code}: {resp2.text[:200]}"}
            return {"ok": False, "error": f"HTTP {resp.status_code}: {body[:200]}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:200]}

    async def send(
        self,
        message: str,
        *,
        chat_id: Optional[str] = None,
        subject: Optional[str] = None,
        silent: bool = False,
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        target = chat_id or self.chat_id
        if not self.bot_token or not target:
            return {"ok": False, "channel": self.name, "error": "not configured"}
        text = f"*{subject}*\n\n{message}" if subject else message
        if len(text) > 4000:
            text = text[:3990] + "\n…"
        payload: Dict[str, Any] = {
            "chat_id": target,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
            "disable_notification": bool(silent),
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = await self._post("sendMessage", payload)
        return {"ok": bool(res.get("ok")), "channel": self.name,
                "silent": silent, "error": res.get("error")}

    async def send_with_menu(
        self, message: str, *, chat_id: Optional[str] = None, silent: bool = True
    ) -> Dict[str, Any]:
        """Send a message and (re)attach the persistent reply keyboard."""
        target = chat_id or self.chat_id
        payload = {
            "chat_id": target,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
            "disable_notification": bool(silent),
            "reply_markup": PERSISTENT_REPLY_KEYBOARD,
        }
        return await self._post("sendMessage", payload)

    async def answer_callback(self, callback_query_id: str, text: str = "") -> Dict[str, Any]:
        return await self._post(
            "answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text}
        )

    async def set_webhook(self, webhook_url: str, secret_token: Optional[str] = None) -> Dict[str, Any]:
        if not self.bot_token:
            return {"ok": False, "error": "TELEGRAM_BOT_TOKEN unset"}
        payload: Dict[str, Any] = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._post("setWebhook", payload)

    async def delete_webhook(self) -> Dict[str, Any]:
        if not self.bot_token:
            return {"ok": False, "error": "TELEGRAM_BOT_TOKEN unset"}
        return await self._post("deleteWebhook", {"drop_pending_updates": False})

    async def get_webhook_info(self) -> Dict[str, Any]:
        if not self.bot_token:
            return {"ok": False, "error": "TELEGRAM_BOT_TOKEN unset"}
        return await self._post("getWebhookInfo", {})


# ---------------------------------------------------------------------------
# Email channel (secondary, optional) — reuses the project's SMTP config.
# ---------------------------------------------------------------------------
class EmailChannel:
    name = "email"

    def is_configured(self) -> bool:
        return bool((getattr(settings, "SMTP_HOST", None) or "").strip())

    async def send(
        self, message: str, *, subject: Optional[str] = None,
        silent: bool = False, reply_markup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        to_addr = os.environ.get("NOTIFICATION_EMAIL_TO") or getattr(settings, "SMTP_USERNAME", None)
        if not self.is_configured() or not to_addr:
            return {"ok": False, "channel": self.name, "error": "not configured"}
        try:
            from app.services.email import send_email  # best-effort reuse

            ok, detail = await send_email(to_addr, subject or "Banking notification", message)
            return {"ok": bool(ok), "channel": self.name, "error": None if ok else detail}
        except Exception as exc:
            return {"ok": False, "channel": self.name, "error": str(exc)[:200]}


# ---------------------------------------------------------------------------
# Simple per-chat conversation state (in-memory; single-instance deployments).
# ---------------------------------------------------------------------------
_chat_state: Dict[str, Dict[str, Any]] = {}
_STATE_TTL = 1800.0  # 30 minutes


def _set_state(chat_id: str, phase: str, **extra: Any) -> None:
    _chat_state[chat_id] = {"phase": phase, "ts": time.monotonic(), **extra}


def _get_state(chat_id: str) -> Optional[Dict[str, Any]]:
    st = _chat_state.get(chat_id)
    if not st:
        return None
    if time.monotonic() - st.get("ts", 0) > _STATE_TTL:
        _chat_state.pop(chat_id, None)
        return None
    return st


def _clear_state(chat_id: str) -> None:
    _chat_state.pop(chat_id, None)


# ---------------------------------------------------------------------------
# The service
# ---------------------------------------------------------------------------
class TelegramService:
    """Outbound notifications + inbound command handling."""

    def _telegram(self) -> TelegramChannel:
        return TelegramChannel(
            bot_token=getattr(settings, "TELEGRAM_BOT_TOKEN", None),
            chat_id=getattr(settings, "TELEGRAM_CHAT_ID", None),
        )

    def _channels(self) -> List[Any]:
        return [self._telegram(), EmailChannel()]

    # -- status ----------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        prefs = get_prefs()
        tg = self._telegram()
        email = EmailChannel()
        status: Dict[str, Any] = {
            "prefs": prefs,
            "allowed_chat_ids": allowed_chat_ids(),
            "channels": {},
            "events_registry": {
                k: {"label": v["label"], "help": v["help"],
                    "icon": v.get("icon", ""), "group": v.get("group", "system")}
                for k, v in EVENT_REGISTRY.items()
            },
            "event_groups": EVENT_GROUPS,
        }
        for ch in (tg, email):
            ch_prefs = prefs.get("channels", {}).get(ch.name, {})
            status["channels"][ch.name] = {
                "configured_via_env": ch.is_configured(),
                "enabled_pref": bool(ch_prefs.get("enabled", True)),
                "ready": ch.is_configured() and bool(ch_prefs.get("enabled", True)),
            }
        return status

    # -- outbound --------------------------------------------------------
    async def notify_event(
        self,
        event: str,
        message: str,
        *,
        subject: Optional[str] = None,
        priority: str = "low",
        silent: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Send ``event`` to every ready channel, honouring user prefs."""
        prefs = get_prefs()
        events = prefs.get("events", {})
        meta = EVENT_REGISTRY.get(event, {})
        if not events.get(event, meta.get("default_enabled", False)):
            return []
        if PRIORITY_RANK.get(priority, 0) < PRIORITY_RANK.get(prefs.get("min_priority", "low"), 0):
            return []
        if silent is None:
            with_sound = bool(prefs.get("sound", {}).get(event, meta.get("default_sound", False)))
            silent = not with_sound

        reply_markup = None
        if prefs.get("include_buttons", True):
            reply_markup = build_inline_keyboard(prefs.get("app_base_url", ""), event)

        results: List[Dict[str, Any]] = []
        for ch in self._channels():
            if not ch.is_configured():
                continue
            if not prefs.get("channels", {}).get(ch.name, {}).get("enabled", True):
                continue
            try:
                if ch.name == "telegram":
                    res = await ch.send(message, subject=subject, silent=silent, reply_markup=reply_markup)
                else:
                    res = await ch.send(message, subject=subject, silent=silent)
            except Exception as exc:
                res = {"ok": False, "channel": ch.name, "error": str(exc)[:200]}
            results.append(res)
        return results

    async def test_send(self) -> List[Dict[str, Any]]:
        return await self.notify_event(
            "manual_test",
            "🧪 پیام تست از سیستم عملیات بانکی — اتصال تلگرام برقرار است.",
            priority="low",
        )

    # -- webhook lifecycle ----------------------------------------------
    async def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
        res = await self._telegram().set_webhook(webhook_url, secret_token=secret)
        return {"ok": bool(res.get("ok")), "result": res}

    async def delete_webhook(self) -> Dict[str, Any]:
        res = await self._telegram().delete_webhook()
        return {"ok": bool(res.get("ok")), "result": res}

    async def webhook_info(self) -> Dict[str, Any]:
        return await self._telegram().get_webhook_info()

    async def ensure_webhook(self) -> Dict[str, Any]:
        """Best-effort: point Telegram at our public webhook if we can derive a
        public URL and it isn't already set. Called at startup."""
        tg = self._telegram()
        if not tg.is_configured():
            return {"ok": False, "skipped": "not_configured"}
        base = ""
        for key in ("BACKEND_PUBLIC_URL", "RENDER_EXTERNAL_URL", "PUBLIC_URL"):
            v = (os.environ.get(key) or "").strip().rstrip("/")
            if v:
                base = v
                break
        if not base:
            return {"ok": False, "skipped": "no_public_url"}
        target = f"{base}/api/telegram/webhook"
        try:
            info = await tg.get_webhook_info()
            current = ((info or {}).get("result") or {}).get("url") or ""
            if current == target:
                return {"ok": True, "unchanged": True, "url": target}
        except Exception:
            pass
        return await self.set_webhook(target)

    # -- inbound (webhook updates) --------------------------------------
    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Process one Telegram update. Never raises (router also guards)."""
        try:
            cq = update.get("callback_query")
            if cq:
                return await self._handle_callback(cq)
            return await self._handle_message(update.get("message") or {})
        except Exception as exc:
            logger.exception("telegram handle_update crashed: %s", exc)
            return {"ok": True, "error": str(exc)[:200]}

    async def _handle_callback(self, cq: Dict[str, Any]) -> Dict[str, Any]:
        tg = self._telegram()
        cq_id = cq.get("id")
        chat_id = (((cq.get("message") or {}).get("chat")) or {}).get("id")
        data = cq.get("data") or ""
        if cq_id:
            await tg.answer_callback(cq_id)
        if not is_allowed(chat_id):
            return {"ok": True, "ignored": True}
        # Inline callbacks map onto the same command handlers.
        if data:
            return await self._dispatch_command(str(chat_id), f"/{data.lstrip('/')}", "")
        return {"ok": True}

    async def _handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        text = (msg.get("text") or "").strip()
        if not chat_id or not text:
            return {"ok": True, "ignored": True}
        chat_id_str = str(chat_id)
        tg = self._telegram()

        # Bootstrap: no allow-list yet → help the operator find their chat id.
        if not allowed_chat_ids():
            await tg.send(
                "👋 ربات فعال است اما هنوز هیچ chat_id مجازی تنظیم نشده.\n\n"
                f"شناسهٔ این گفتگو:\n`{chat_id_str}`\n\n"
                "این مقدار را در env (`TELEGRAM_CHAT_ID`) یا در تب تلگرامِ تنظیمات پنل "
                "اضافه کنید تا دستورها فعال شوند.",
                chat_id=chat_id_str,
            )
            return {"ok": True, "handled": "bootstrap"}

        if not is_allowed(chat_id_str):
            logger.info("telegram: ignoring chat %s (not in allow-list)", chat_id_str)
            return {"ok": True, "ignored": True}

        # Reply-keyboard button text → command.
        if text in TEXT_ALIASES:
            _clear_state(chat_id_str)
            text = TEXT_ALIASES[text]

        # Continue an in-progress flow (currently: awaiting an AI question).
        state = _get_state(chat_id_str)
        if state and state.get("phase") == "awaiting_ai" and not text.startswith("/"):
            _clear_state(chat_id_str)
            return await self._cmd_ai(chat_id_str, text)

        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            command = parts[0].split("@")[0].lower()  # strip @botname
            arg = parts[1] if len(parts) > 1 else ""
            return await self._dispatch_command(chat_id_str, command, arg)

        # Free text (no command, not a menu button) → treat as an AI question.
        return await self._cmd_ai(chat_id_str, text)

    async def _dispatch_command(self, chat_id: str, command: str, arg: str) -> Dict[str, Any]:
        handlers = {
            "/start": self._cmd_menu,
            "/menu": self._cmd_menu,
            "/help": self._cmd_help,
            "/ping": self._cmd_ping,
            "/status": self._cmd_status,
            "/stats": self._cmd_stats,
            "/expiring": self._cmd_expiring,
            "/fx": self._cmd_fx,
            "/scan": self._cmd_scan,
            "/backup": self._cmd_backup,
        }
        if command == "/ai":
            return await self._cmd_ai(chat_id, arg)
        handler = handlers.get(command)
        if handler is None:
            await self._telegram().send(
                f"دستور ناشناخته: `{command}`\nبرای فهرست دستورها /help را بزنید.",
                chat_id=chat_id, silent=True,
            )
            return {"ok": True, "handled": "unknown"}
        return await handler(chat_id)

    # -- command handlers ------------------------------------------------
    async def _cmd_menu(self, chat_id: str) -> Dict[str, Any]:
        await self._telegram().send_with_menu(
            "🏦 *سیستم عملیات بانکی*\nاز منوی پایین یک گزینه انتخاب کن یا سؤالت را تایپ کن.",
            chat_id=chat_id,
        )
        return {"ok": True, "handled": "menu"}

    async def _cmd_help(self, chat_id: str) -> Dict[str, Any]:
        await self._telegram().send(
            "*دستورهای موجود:*\n"
            "📊 /status — وضعیت سیستم\n"
            "📈 /stats — آمار پرتفوی\n"
            "🏦 /expiring — تسهیلات و مدارک رو به انقضا\n"
            "💱 /fx — نرخ‌های ارز\n"
            "🔁 /scan — اجرای اسکن انقضا و ساخت آلرت‌ها\n"
            "☁️ /backup — پشتیبان‌گیری/سینک دستی\n"
            "🤖 /ai <سؤال> — پرسش از هوش مصنوعی\n"
            "📋 /menu — نمایش منوی ثابت\n\n"
            "هر متن آزادی که بفرستی به‌عنوان سؤال به هوش مصنوعی فرستاده می‌شود.",
            chat_id=chat_id, silent=True,
        )
        return {"ok": True, "handled": "help"}

    async def _cmd_ping(self, chat_id: str) -> Dict[str, Any]:
        await self._telegram().send("🏓 pong — backend در دسترس است.", chat_id=chat_id, silent=True)
        return {"ok": True, "handled": "ping"}

    async def _cmd_status(self, chat_id: str) -> Dict[str, Any]:
        from app.database import AsyncSessionLocal
        lines = ["📊 *وضعیت سیستم*"]
        try:
            from sqlalchemy import select, func
            from app.models.customer import Customer
            from app.models.facility import Facility
            async with AsyncSessionLocal() as db:
                cust = (await db.execute(
                    select(func.count(Customer.id)).where(Customer.is_deleted == False)  # noqa: E712
                )).scalar() or 0
                fac = (await db.execute(
                    select(func.count(Facility.id)).where(Facility.is_deleted == False)  # noqa: E712
                )).scalar() or 0
            lines.append("🟢 پایگاه‌داده: سالم")
            lines.append(f"👥 مشتریان: *{cust:,}*")
            lines.append(f"🏦 تسهیلات: *{fac:,}*")
        except Exception as exc:
            lines.append(f"🔴 پایگاه‌داده: خطا — `{str(exc)[:120]}`")
        lines.append(f"⚙️ نسخه: {getattr(settings, 'APP_VERSION', '?')}  ·  محیط: {getattr(settings, 'ENVIRONMENT', '?')}")
        await self._telegram().send("\n".join(lines), chat_id=chat_id, silent=True)
        return {"ok": True, "handled": "status"}

    async def _cmd_stats(self, chat_id: str) -> Dict[str, Any]:
        from app.database import AsyncSessionLocal
        try:
            from sqlalchemy import select, func
            from app.models.customer import Customer
            from app.models.facility import Facility
            from app.services.fx import load_rates, to_base
            async with AsyncSessionLocal() as db:
                total_cust = (await db.execute(
                    select(func.count(Customer.id)).where(Customer.is_deleted == False)  # noqa: E712
                )).scalar() or 0
                total_fac = (await db.execute(
                    select(func.count(Facility.id)).where(Facility.is_deleted == False)  # noqa: E712
                )).scalar() or 0
                rates = await load_rates(db)
                rows = (await db.execute(
                    select(Facility.amount, Facility.currency).where(Facility.is_deleted == False)  # noqa: E712
                )).all()
                exposure = sum(to_base(a, c, rates) for a, c in rows)
            from app.models.exchange_rate import BASE_CURRENCY
            text = (
                "📈 *آمار پرتفوی*\n"
                f"👥 مشتریان: *{total_cust:,}*\n"
                f"🏦 تسهیلات: *{total_fac:,}*\n"
                f"💰 مجموع exposure: *{exposure:,.0f} {BASE_CURRENCY}*"
            )
        except Exception as exc:
            text = f"⚠️ خطا در محاسبهٔ آمار: `{str(exc)[:150]}`"
        await self._telegram().send(text, chat_id=chat_id, silent=True)
        return {"ok": True, "handled": "stats"}

    async def _cmd_expiring(self, chat_id: str) -> Dict[str, Any]:
        from app.database import AsyncSessionLocal
        try:
            from datetime import date
            from sqlalchemy import select, func
            from app.models.customer import Customer
            from app.models.facility import Facility
            from app.models.system_setting import SystemSetting
            today = date.today()
            async with AsyncSessionLocal() as db:
                wd_row = (await db.execute(
                    select(SystemSetting).where(SystemSetting.key == "expiry_warning_days")
                )).scalar_one_or_none()
                try:
                    wd = int(wd_row.value) if wd_row and wd_row.value else 30
                except (TypeError, ValueError):
                    wd = 30
                rows = (await db.execute(
                    select(Facility, Customer.account_no)
                    .join(Customer, Facility.customer_id == Customer.id)
                    .where(Facility.is_deleted == False)  # noqa: E712
                )).all()
            items = []
            for fac, acc in rows:
                exp = fac.expiry_date or fac.end_date
                if not exp:
                    continue
                days_left = (exp - today).days
                if days_left > wd:
                    continue
                name = fac.name or (getattr(fac.facility_type, "value", fac.facility_type) or "facility")
                items.append((days_left, acc, name, exp))
            items.sort(key=lambda x: x[0])
            if not items:
                text = f"✅ هیچ تسهیلاتی در {wd} روز آینده به انقضا نمی‌رسد."
            else:
                head = f"🏦 *{len(items)} تسهیلات رو به انقضا* (پنجرهٔ {wd} روز):\n"
                body = []
                for days_left, acc, name, exp in items[:15]:
                    flag = "⛔️ منقضی" if days_left < 0 else f"⏳ {days_left} روز"
                    body.append(f"• {flag} — {name} ({acc}) — {exp.isoformat()}")
                if len(items) > 15:
                    body.append(f"… و {len(items) - 15} مورد دیگر")
                text = head + "\n".join(body)
        except Exception as exc:
            text = f"⚠️ خطا در خواندن انقضاها: `{str(exc)[:150]}`"
        await self._telegram().send(text, chat_id=chat_id, silent=True)
        return {"ok": True, "handled": "expiring"}

    async def _cmd_fx(self, chat_id: str) -> Dict[str, Any]:
        try:
            from app.services.fx import load_rates
            from app.models.exchange_rate import BASE_CURRENCY
            rates = await load_rates()
            lines = [f"💱 *نرخ ارز* (پایه: {BASE_CURRENCY})"]
            for cur, rate in sorted(rates.items()):
                if cur == BASE_CURRENCY:
                    continue
                lines.append(f"• 1 {cur} = {rate:,.4f} {BASE_CURRENCY}")
            text = "\n".join(lines) if len(lines) > 1 else "نرخی ثبت نشده است."
        except Exception as exc:
            text = f"⚠️ خطا در خواندن نرخ ارز: `{str(exc)[:150]}`"
        await self._telegram().send(text, chat_id=chat_id, silent=True)
        return {"ok": True, "handled": "fx"}

    async def _cmd_scan(self, chat_id: str) -> Dict[str, Any]:
        tg = self._telegram()
        await tg.send("🔁 در حال اجرای اسکن انقضا…", chat_id=chat_id, silent=True)
        try:
            from app.database import AsyncSessionLocal
            from app.services.expiry import run_expiry_scan
            async with AsyncSessionLocal() as db:
                result = await run_expiry_scan(db)
            text = (
                "✅ *اسکن انقضا کامل شد*\n"
                f"• کل آلرت‌ها: *{result.get('total', 0)}*\n"
                f"• تسهیلات: {result.get('facilities', 0)}\n"
                f"• مدارک: {result.get('documents', 0)}\n"
                f"• تسک جدید: {result.get('tasks_created', 0)} · به‌روزشده: {result.get('tasks_updated', 0)}"
            )
        except Exception as exc:
            text = f"⚠️ اسکن ناموفق بود: `{str(exc)[:150]}`"
        await tg.send(text, chat_id=chat_id, silent=False)
        return {"ok": True, "handled": "scan"}

    async def _cmd_backup(self, chat_id: str) -> Dict[str, Any]:
        tg = self._telegram()
        try:
            from app.services import drive_sync
            if not drive_sync.is_enabled():
                await tg.send(
                    "ℹ️ سینک Google Drive فعال نیست. برای فعال‌سازی متغیرهای "
                    "`GOOGLE_DRIVE_ENABLED`، `GOOGLE_CREDENTIALS_JSON` و "
                    "`GOOGLE_DRIVE_FOLDER_ID` را تنظیم کنید.",
                    chat_id=chat_id, silent=True,
                )
                return {"ok": True, "handled": "backup_disabled"}
            await tg.send("☁️ در حال پشتیبان‌گیری/سینک با Google Drive…", chat_id=chat_id, silent=True)
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                res = await drive_sync.sync_database_snapshot(db, reason="telegram")
            ok = bool(res.get("ok", True)) and not res.get("error")
            if ok:
                size = res.get("bytes")
                extra = f" ({round(size / 1024)} KB)" if size else ""
                text = f"✅ پشتیبان‌گیری انجام شد{extra}."
            else:
                text = f"🛑 پشتیبان‌گیری ناموفق: `{str(res.get('error'))[:150]}`"
            await tg.send(text, chat_id=chat_id, silent=not ok)
        except Exception as exc:
            await tg.send(f"🛑 خطا در پشتیبان‌گیری: `{str(exc)[:150]}`", chat_id=chat_id, silent=False)
        return {"ok": True, "handled": "backup"}

    async def _cmd_ai(self, chat_id: str, question: str) -> Dict[str, Any]:
        tg = self._telegram()
        question = (question or "").strip()
        if not question:
            _set_state(chat_id, "awaiting_ai")
            await tg.send("🤖 سؤالت را بنویس تا از هوش مصنوعی بپرسم:", chat_id=chat_id, silent=True)
            return {"ok": True, "handled": "ai_prompt"}
        await tg.send("🤖 در حال فکر کردن…", chat_id=chat_id, silent=True)
        try:
            from app.database import AsyncSessionLocal
            from app.ai.inference import complete
            system = (
                "تو دستیار یک سیستم عملیات بانکی هستی. کوتاه، دقیق و به زبان کاربر پاسخ بده."
            )
            async with AsyncSessionLocal() as db:
                res = await complete(db, question, task="chat", system=system, max_tokens=1024)
            if res.get("ok"):
                answer = res.get("text") or "(پاسخ خالی)"
                model = res.get("model")
                suffix = f"\n\n_— {model}_" if model else ""
                await tg.send(answer + suffix, chat_id=chat_id, silent=True)
            elif res.get("error") == "no_model":
                await tg.send(
                    "⚠️ هیچ مدل هوش مصنوعی پیکربندی نشده. در تنظیمات پنل (تب AI) یک "
                    "ارائه‌دهنده و کلید اضافه کنید.",
                    chat_id=chat_id, silent=True,
                )
            else:
                await tg.send(f"⚠️ خطا در پاسخ AI: `{str(res.get('error'))[:150]}`", chat_id=chat_id, silent=True)
        except Exception as exc:
            await tg.send(f"⚠️ خطا در پردازش سؤال: `{str(exc)[:150]}`", chat_id=chat_id, silent=True)
        return {"ok": True, "handled": "ai"}


# Module-level singleton.
telegram_service = TelegramService()


async def notify_event_async(event: str, message: str, **kwargs: Any) -> List[Dict[str, Any]]:
    """Convenience wrapper for callers that already run in an event loop."""
    return await telegram_service.notify_event(event, message, **kwargs)
