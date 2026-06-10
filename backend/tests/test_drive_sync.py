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


class TestConfigGating:
    def test_configured_requires_all_three(self, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_ENABLED", True)
        monkeypatch.setattr(settings, "GOOGLE_CREDENTIALS_JSON", "")
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_FOLDER_ID", "")
        assert settings.google_drive_configured() is False

        monkeypatch.setattr(settings, "GOOGLE_CREDENTIALS_JSON", '{"x": 1}')
        monkeypatch.setattr(settings, "GOOGLE_DRIVE_FOLDER_ID", "folder123")
        assert settings.google_drive_configured() is True
