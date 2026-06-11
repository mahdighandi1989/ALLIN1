"""Google Drive sync: naming convention, graceful no-op, and config gating.

These tests deliberately avoid any real network/Drive calls — they exercise the
pure naming logic and the "disabled is a safe no-op" contract that keeps a Drive
misconfiguration from ever breaking uploads or startup.
"""
import re

import pytest

from app.config import settings
from app.services import drive_sync


class TestNaming:
    def test_build_name_is_traceable_and_structured(self):
        name = drive_sync.build_name("attachment", "cust-1001", "fac-F1--passport", "pdf")
        # allin1__<category>__<owner>__<descriptor>__<stamp>__<shortid>.pdf
        assert name.startswith("allin1__attachment__cust-1001__fac-F1--passport__")
        assert name.endswith(".pdf")
        fields = name[: -len(".pdf")].split("__")
        assert fields[0] == "allin1"
        assert fields[1] == "attachment"
        assert fields[2] == "cust-1001"
        # UTC stamp + 6-char short id are the last two fields.
        assert re.fullmatch(r"\d{8}-\d{6}Z", fields[-2])
        assert re.fullmatch(r"[0-9a-f]{6}", fields[-1])

    def test_fields_cannot_forge_the_separator(self):
        # Stray separators / unsafe chars in a field must not break parsing.
        name = drive_sync.build_name("att__ack", "cust 1001", "weird/name spaces", "json")
        body = name[: -len(".json")]
        # Exactly the six structural fields — no extra splits from injected '__'.
        assert len(body.split("__")) == 6

    def test_build_name_without_extension(self):
        name = drive_sync.build_name("db-snapshot", "system", "full", "")
        assert "." not in name.split("__")[-1]  # short id has no extension


class TestDisabledNoOp:
    async def test_attachment_sync_is_noop_when_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_ENABLED", False)
        res = await drive_sync.sync_attachment(
            account_no="1001", facility_id="F1", original_name="x.pdf", data=b"hi"
        )
        assert res == {"ok": False, "skipped": True, "reason": "drive_sync_disabled"}

    async def test_status_reports_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_ENABLED", False)
        st = await drive_sync.status()
        assert st["configured"] is False
        assert st["connected"] is False

    async def test_status_oauth_not_connected(self, monkeypatch):
        # OAuth mode + client creds set, but no refresh token stored yet.
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_ENABLED", True)
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_AUTH_MODE", "oauth")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")

        from app.services import drive_settings

        async def _none():
            return None

        monkeypatch.setattr(drive_settings, "resolve_refresh_token", _none)
        monkeypatch.setattr(drive_settings, "connected_account", _none)

        st = await drive_sync.status()
        assert st["mode"] == "oauth"
        assert st["connected"] is False
        assert st["error"] == "not_connected"


class TestDrivePrimaryStorage:
    """End-to-end attachment flow with Drive as the primary store (mocked Drive).

    Verifies the routing logic without any real network: an upload lands in Drive
    (not on disk), download streams the Drive bytes back, and delete removes it
    from Drive.
    """

    async def test_upload_download_delete_via_drive(
        self, client, auth_headers, test_customer, tmp_path, monkeypatch
    ):
        from app.services import drive_sync
        from app.services import attachments as store

        # Point disk store at a temp dir so we can assert nothing is written there.
        monkeypatch.setattr(store, "UPLOAD_DIR", tmp_path)

        # In-memory fake Drive.
        fake_drive: dict[str, bytes] = {}

        async def fake_sync_attachment(*, account_no, facility_id, original_name, data, mimetype="application/octet-stream"):
            fid = f"drive-{len(fake_drive) + 1}"
            fake_drive[fid] = data
            return {"ok": True, "result": {"id": fid, "name": f"allin1__attachment__{fid}.bin"}}

        async def fake_download(file_id):
            return fake_drive[file_id]

        async def fake_delete(file_id):
            fake_drive.pop(file_id, None)
            return {"ok": True}

        monkeypatch.setattr(drive_sync, "is_enabled", lambda: True)
        monkeypatch.setattr(drive_sync, "sync_attachment", fake_sync_attachment)
        monkeypatch.setattr(drive_sync, "download_attachment", fake_download)
        monkeypatch.setattr(drive_sync, "delete_attachment", fake_delete)

        acc = test_customer.account_no
        files = {"file": ("report.pdf", b"%PDF-1.4 binary", "application/pdf")}
        r = await client.post(f"/api/crm/attachments/{acc}", headers=auth_headers, files=files)
        assert r.status_code == 200, r.text
        body = r.json()
        aid = body["id"]
        assert body["storage"] == "drive"  # stored in Drive, not on disk

        # Nothing was written to the local disk store.
        assert not any(tmp_path.rglob("*.pdf"))
        # The byte content really lives in (fake) Drive.
        assert b"%PDF-1.4 binary" in fake_drive.values()

        # Download pulls the bytes back from Drive.
        dl = await client.get(f"/api/crm/attachments/{aid}/download", headers=auth_headers)
        assert dl.status_code == 200
        assert dl.content == b"%PDF-1.4 binary"

        # Delete removes it from Drive and from the listing.
        x = await client.delete(f"/api/crm/attachments/{aid}", headers=auth_headers)
        assert x.status_code == 200
        assert fake_drive == {}

    async def test_upload_falls_back_to_disk_when_drive_fails(
        self, client, auth_headers, test_customer, tmp_path, monkeypatch
    ):
        from app.services import drive_sync
        from app.services import attachments as store

        monkeypatch.setattr(store, "UPLOAD_DIR", tmp_path)

        async def failing_sync(*args, **kwargs):
            return {"ok": False, "error": "boom"}

        monkeypatch.setattr(drive_sync, "is_enabled", lambda: True)
        monkeypatch.setattr(drive_sync, "sync_attachment", failing_sync)

        acc = test_customer.account_no
        files = {"file": ("fallback.txt", b"keep me", "text/plain")}
        r = await client.post(f"/api/crm/attachments/{acc}", headers=auth_headers, files=files)
        assert r.status_code == 200, r.text
        assert r.json()["storage"] == "disk"  # fell back to disk, upload not lost

        dl = await client.get(f"/api/crm/attachments/{r.json()['id']}/download", headers=auth_headers)
        assert dl.status_code == 200
        assert dl.content == b"keep me"


class TestConfigGating:
    def test_oauth_mode_requires_client_credentials(self, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_ENABLED", True)
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_AUTH_MODE", "oauth")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")
        assert settings.google_drive_configured() is False

        monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
        monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")
        # OAuth mode is "configured" with just the client creds (the refresh token
        # lives in the DB and is checked at sync time, not here).
        assert settings.google_drive_configured() is True

    def test_service_account_mode_requires_creds_and_folder(self, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_ENABLED", True)
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_AUTH_MODE", "service_account")
        monkeypatch.setattr(settings, "GOOGLE_CREDENTIALS_JSON", "")
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_FOLDER_ID", "")
        assert settings.google_drive_configured() is False

        monkeypatch.setattr(settings, "GOOGLE_CREDENTIALS_JSON", '{"x": 1}')
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_FOLDER_ID", "folder123")
        assert settings.google_drive_configured() is True

    def test_disabled_is_never_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_ENABLED", False)
        assert settings.google_drive_configured() is False


class TestHttpErrorDescription:
    """The 403 cause + fix hint must lead the message, surviving truncation."""

    class _FakeResp:
        def __init__(self, status):
            self.status = status

    class _FakeHttpError(Exception):
        def __init__(self, status, content):
            self.resp = TestHttpErrorDescription._FakeResp(status)
            self.content = content

    def test_storage_quota_exceeded_surfaces_reason_and_fix(self):
        from app.services import google_drive as gd

        content = (
            b'{"error": {"code": 403, "message": "Service Accounts do not have '
            b'storage quota.", "errors": [{"reason": "storageQuotaExceeded"}]}}'
        )
        exc = self._FakeHttpError(403, content)
        err = gd._drive_error("upload 'x.json'", exc)
        msg = str(err)
        assert "403 storageQuotaExceeded" in msg
        assert "Fix:" in msg  # actionable hint included

    def test_non_http_error_falls_back_to_generic(self):
        from app.services import google_drive as gd

        err = gd._drive_error("upload 'x.json'", ValueError("boom"))
        assert "ValueError" in str(err)
