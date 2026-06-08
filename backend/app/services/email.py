"""Lightweight SMTP email sender, driven by the SMTP_* settings.

Powers the credit-summary / reminder emails (the Excel SendUnsentNotesToEmail /
DailyReport feature). It is a graceful no-op with a clear message when SMTP is
not configured, so the app keeps working until the operator sets the env vars on
Render (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS).
"""
import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool((settings.SMTP_HOST or "").strip())


def _send_sync(to: list[str], subject: str, text_body: str, html_body: str | None) -> tuple[bool, str]:
    host = (settings.SMTP_HOST or "").strip()
    if not host:
        return False, "SMTP is not configured. Set SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD on the server."
    sender = (settings.SMTP_USERNAME or "no-reply@localhost").strip()
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(host, settings.SMTP_PORT, timeout=20) as s:
            if settings.SMTP_USE_TLS:
                s.starttls(context=ssl.create_default_context())
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            s.send_message(msg)
        return True, "sent"
    except Exception as exc:  # pragma: no cover - depends on a live SMTP server
        logger.warning("email send failed: %s", exc)
        return False, f"Email send failed: {exc}"


async def send_email(to, subject: str, text_body: str, html_body: str | None = None) -> tuple[bool, str]:
    """Send an email off the event loop. Returns (ok, message)."""
    if isinstance(to, str):
        to = [to]
    to = [t.strip() for t in (to or []) if t and t.strip()]
    if not to:
        return False, "No recipient address."
    return await asyncio.to_thread(_send_sync, to, subject, text_body, html_body)
