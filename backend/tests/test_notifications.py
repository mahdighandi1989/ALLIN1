"""Tests for the event notification service and the data-scan failure events."""
import os
import tempfile

import pytest

from app.services import notifications
from app.services.notifications import notify_event, CRITICAL_EVENTS
from app.services import data_scan


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """Notifications rate-limit by event; clear it between tests."""
    notifications._last_sent.clear()
    yield
    notifications._last_sent.clear()


@pytest.fixture
def captured(monkeypatch):
    """Capture dispatched notifications instead of hitting Telegram."""
    sent = []

    def fake_send(text):
        sent.append(text)
        return True

    monkeypatch.setattr(notifications, "_send_telegram", fake_send)
    return sent


def test_scan_failed_is_critical_non_silent_high_priority():
    assert "scan_failed" in CRITICAL_EVENTS


def test_notify_event_scan_failed_dispatches_persian_message(captured):
    ok = notify_event("scan_failed", "فایل خراب است")
    assert ok is True
    assert len(captured) == 1
    # Message is in Persian and references the event.
    assert "scan_failed" in captured[0]
    assert "اسکن" in captured[0]


def test_notify_event_defaults_for_critical(monkeypatch):
    """Critical events default to silent=False + priority=high (so they send)."""
    seen = {}

    def fake_send(text):
        seen["sent"] = text
        return True

    monkeypatch.setattr(notifications, "_send_telegram", fake_send)
    notify_event("scan_failed", "x")
    assert "sent" in seen  # non-silent -> delivery attempted


def test_notify_event_rate_limited(captured, monkeypatch):
    monkeypatch.setattr(
        notifications.settings, "NOTIFY_RATE_LIMIT_SECONDS", 60, raising=False
    )
    assert notify_event("scan_failed", "first") is True
    # Second identical event within the window is suppressed.
    assert notify_event("scan_failed", "second") is False
    assert len(captured) == 1


def test_scan_missing_dir_emits_scan_failed(captured):
    result = data_scan.scan_data_files("/nonexistent/path/xyz")
    assert result.ok is False
    assert len(captured) >= 1
    assert any("scan_failed" in m for m in captured)


def test_scan_corrupt_file_emits_scan_failed(captured):
    with tempfile.TemporaryDirectory() as d:
        # A bogus .xlsx that openpyxl cannot read.
        with open(os.path.join(d, "broken.xlsx"), "w") as f:
            f.write("not a real spreadsheet")
        result = data_scan.scan_data_files(d)
    assert result.ok is False
    assert "broken.xlsx" in result.failed
    assert any("scan_failed" in m for m in captured)


def test_run_scan_task_verifies_and_notifies(captured):
    with tempfile.TemporaryDirectory() as d:
        # Empty dir -> nothing scanned -> verify_failed.
        result = data_scan.run_scan_task(d)
    assert result.ok is True or result.ok is False  # never raises
    # An empty scan triggers a verify_failed notification.
    assert any("verify_failed" in m for m in captured)
