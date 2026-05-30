"""Logging filter that redacts sensitive values from log records.

Even though the application code is careful never to log raw credentials, this
filter is a defence-in-depth guarantee: any log line (including ones emitted by
third-party libraries or future code) that happens to contain a ``password``,
``token``, ``secret``, ``authorization`` or similar value has that value
replaced with ``***REDACTED***`` before it is written to any handler.
"""
from __future__ import annotations

import logging
import re
from typing import List, Pattern

# Keys whose associated values must never appear in logs.
_SENSITIVE_KEYS = [
    "password",
    "passwd",
    "pwd",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "authorization",
    "api_key",
    "apikey",
    "hashed_password",
]

_REDACTION = "***REDACTED***"


def _build_patterns() -> List[Pattern[str]]:
    patterns: List[Pattern[str]] = []
    for key in _SENSITIVE_KEYS:
        # key="value" / key='value' / key=value / key: value / "key": "value"
        patterns.append(
            re.compile(
                rf"(?i)([\"']?{re.escape(key)}[\"']?\s*[:=]\s*)"
                rf"([\"']?)([^\s,;}}\"']+)([\"']?)"
            )
        )
    # "Bearer <token>" anywhere in the message.
    patterns.append(re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._\-]+)"))
    return patterns


_PATTERNS = _build_patterns()


def sanitize(message: str) -> str:
    """Return ``message`` with any sensitive values redacted."""
    if not message:
        return message
    redacted = message
    for pattern in _PATTERNS:
        if pattern.pattern.startswith("(?i)(bearer"):
            redacted = pattern.sub(rf"\1{_REDACTION}", redacted)
        else:
            redacted = pattern.sub(rf"\1\2{_REDACTION}\4", redacted)
    return redacted


class SensitiveDataFilter(logging.Filter):
    """A :class:`logging.Filter` that scrubs sensitive data from every record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 - stdlib name
        try:
            message = record.getMessage()
            sanitized = sanitize(message)
            if sanitized != message:
                record.msg = sanitized
                record.args = ()
        except Exception:
            # Never let logging hygiene break the actual log call.
            pass
        return True


def install_log_sanitizer() -> None:
    """Attach :class:`SensitiveDataFilter` to the root logger and its handlers.

    Idempotent: calling it multiple times will not add duplicate filters.
    """
    root = logging.getLogger()
    if not any(isinstance(f, SensitiveDataFilter) for f in root.filters):
        root.addFilter(SensitiveDataFilter())
    for handler in root.handlers:
        if not any(isinstance(f, SensitiveDataFilter) for f in handler.filters):
            handler.addFilter(SensitiveDataFilter())
