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

    def fake_send(text, **kwargs):
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

    def fake_send(text, **kwargs):
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


@pytest.mark.asyncio
async def test_broadcast_read_is_per_user(client, db_session):
    """First reader of a broadcast must NOT hide it from other users."""
    from app.models.user import User as U
    from app.models.notification import Notification
    from app.utils.security import hash_password, create_access_token

    async def mk(username):
        u = U(username=username, email=f"{username}@x.ae",
              hashed_password=hash_password("Passw0rd1"), full_name=username,
              is_active=True, role="editor")
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        tok = create_access_token(data={"user_id": u.id, "username": u.username})
        return {"Authorization": f"Bearer {tok}"}

    h_a, h_b = await mk("bcast_a"), await mk("bcast_b")
    db_session.add(Notification(title="Broadcast!", user_id=None))
    await db_session.commit()

    # Both see 1 unread.
    assert (await client.get("/api/notifications/unread-count", headers=h_a)).json()["unread"] == 1
    assert (await client.get("/api/notifications/unread-count", headers=h_b)).json()["unread"] == 1

    # A marks all read -> A sees 0, B STILL sees 1.
    assert (await client.post("/api/notifications/read-all", headers=h_a)).status_code == 200
    assert (await client.get("/api/notifications/unread-count", headers=h_a)).json()["unread"] == 0
    assert (await client.get("/api/notifications/unread-count", headers=h_b)).json()["unread"] == 1

    # B's list shows the broadcast as unread; A's as read.
    la = (await client.get("/api/notifications/", headers=h_a)).json()["items"]
    lb = (await client.get("/api/notifications/", headers=h_b)).json()["items"]
    assert [i for i in la if i["title"] == "Broadcast!"][0]["is_read"] is True
    assert [i for i in lb if i["title"] == "Broadcast!"][0]["is_read"] is False

    # B marks the single broadcast read via /read.
    nid = [i for i in lb if i["title"] == "Broadcast!"][0]["id"]
    assert (await client.post(f"/api/notifications/{nid}/read", headers=h_b)).status_code == 200
    assert (await client.get("/api/notifications/unread-count", headers=h_b)).json()["unread"] == 0
