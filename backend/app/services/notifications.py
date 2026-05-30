"""Event notification service.

Critical system events (e.g. ``scan_failed``, ``verify_failed``,
``task_failed``) are surfaced to operators via :func:`notify_event`. Delivery is
best-effort over the Telegram Bot API when ``TELEGRAM_BOT_TOKEN`` /
``TELEGRAM_CHAT_ID`` are configured; otherwise the notification is logged so the
event is never silently lost. A simple per-event rate limit prevents spam from
high-frequency events.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Events considered critical: they default to non-silent, high priority.
CRITICAL_EVENTS = {"scan_failed", "verify_failed", "task_failed"}

# Persian message templates keyed by event. ``{detail}`` is filled at call time.
EVENT_TEMPLATES: Dict[str, str] = {
    "scan_failed": "🚨 اسکن دادهٔ سیستم با خطا مواجه شد (scan_failed): {detail}",
    "verify_failed": "🚨 راستی‌آزمایی دادهٔ سیستم ناموفق بود (verify_failed): {detail}",
    "task_failed": "🚨 اجرای وظیفهٔ پس‌زمینه ناموفق بود (task_failed): {detail}",
}

# Per-event last-sent timestamps for rate limiting.
_last_sent: Dict[str, float] = {}
_lock = threading.Lock()


def _format_message(event: str, detail: str) -> str:
    template = EVENT_TEMPLATES.get(event)
    if template:
        return template.format(detail=detail or "بدون جزئیات")
    return f"رویداد «{event}»: {detail or 'بدون جزئیات'}"


def _rate_limited(event: str) -> bool:
    window = int(getattr(settings, "NOTIFY_RATE_LIMIT_SECONDS", 60))
    if window <= 0:
        return False
    now = time.monotonic()
    with _lock:
        last = _last_sent.get(event, 0.0)
        if now - last < window:
            return True
        _last_sent[event] = now
    return False


def _send_telegram(text: str) -> bool:
    """Best-effort Telegram delivery. Returns True if sent, False otherwise."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)
    if not token or not chat_id:
        return False
    try:  # pragma: no cover - only exercised when Telegram is configured
        import httpx

        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_notification": False},
            timeout=10.0,
        )
        return resp.status_code == 200
    except Exception as exc:  # pragma: no cover
        logger.warning("Telegram notification delivery failed: %s", exc)
        return False


def notify_event(
    event: str,
    detail: str = "",
    *,
    silent: Optional[bool] = None,
    priority: Optional[str] = None,
    rate_limit: bool = True,
    **context,
) -> bool:
    """Emit a notification for ``event``.

    Critical events default to ``silent=False`` and ``priority="high"``. Returns
    ``True`` if a notification was dispatched/logged, ``False`` if it was
    suppressed by the rate limiter.
    """
    is_critical = event in CRITICAL_EVENTS
    if silent is None:
        silent = False if is_critical else True
    if priority is None:
        priority = "high" if is_critical else "normal"

    if rate_limit and _rate_limited(event):
        logger.debug("notify_event rate-limited: %s", event)
        return False

    message = _format_message(event, detail)

    # Always log critical events (defence-in-depth) so they are observable even
    # when Telegram is not configured.
    log = logger.error if is_critical else logger.info
    log("notify_event event=%s priority=%s silent=%s | %s", event, priority, silent, message)

    if not silent:
        _send_telegram(message)
    return True
