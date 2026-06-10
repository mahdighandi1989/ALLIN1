"""App-aware Google Drive sync orchestration.

This layer turns domain events ("a snapshot was taken", "a document was
uploaded") into Drive operations with a consistent, *traceable* layout:

Folder taxonomy (everything lives under the configured GOOGLE_DRIVE_FOLDER_ID):

    <root>/
      backups/database/        <- full DB JSON snapshots
      attachments/cust-<acc>/fac-<fac>/   <- the actual uploaded documents

File naming convention (the name itself carries identity + ownership, and is
sortable/greppable). Fields are separated by ``__`` and never contain ``__``:

    allin1__<category>__<owner>__<descriptor>__<utc-stamp>__<shortid>.<ext>

    e.g.  allin1__db-snapshot__system__full__20260610-202530Z__a1b2c3.json
          allin1__attachment__cust-1001__fac-F1--passport__20260610-202530Z__a1b2c3.pdf

A stable "latest" mirror (no stamp/shortid) is kept beside the timestamped
history for the DB snapshot, updated in place so there is always one current
file that reflects the live state — that is what keeps Drive "in sync" with the
app, while the stamped files give you point-in-time history.

Every public coroutine here is best-effort: if Drive is disabled, unconfigured,
or the call fails, it logs and returns a result dict with ``ok=False`` instead of
raising, so a sync problem can never break an attachment upload or app startup.
The blocking Drive client (``google_drive``) is always called through
``asyncio.to_thread`` so the event loop is never blocked.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services import google_drive
from app.services.backup import build_backup_payload

logger = logging.getLogger(__name__)

_APP = "allin1"
_FIELD_SEP = "__"
# Within a single field we only allow these chars; everything else collapses to
# '-' so the '__' field separator stays unambiguous and names are filesystem- and
# URL-safe wherever they're later downloaded.
_FIELD_UNSAFE = re.compile(r"[^A-Za-z0-9.-]+")


def is_enabled() -> bool:
    """Whether Drive sync is switched on and configured."""
    return google_drive.is_configured()


def _utc_stamp() -> str:
    """Compact, sortable UTC timestamp: 20260610-202530Z."""
    return datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")


def _field(value: str, fallback: str = "na", limit: int = 60) -> str:
    """Sanitize one name field: keep it short, safe, and separator-free."""
    cleaned = _FIELD_UNSAFE.sub("-", str(value or "").strip()).strip("-.")
    cleaned = cleaned.replace(_FIELD_SEP, "-")  # never let a field forge a separator
    return (cleaned or fallback)[:limit]


def build_name(category: str, owner: str, descriptor: str, ext: str) -> str:
    """Compose a traceable file name from its identity fields.

    ``ext`` may be given with or without a leading dot; an empty ext yields a
    name with no extension.
    """
    stamp = _utc_stamp()
    shortid = uuid.uuid4().hex[:6]
    stem = _FIELD_SEP.join(
        [
            _APP,
            _field(category, "misc"),
            _field(owner, "system"),
            _field(descriptor, "item", limit=80),
            stamp,
            shortid,
        ]
    )
    ext = (ext or "").lstrip(".")
    return f"{stem}.{ext}" if ext else stem


def _split_ext(filename: str) -> tuple[str, str]:
    """Split ``name.ext`` into (stem, ext); ext is '' when there's no extension."""
    name = (filename or "").strip()
    if "." in name and not name.endswith("."):
        stem, _, ext = name.rpartition(".")
        return stem, ext
    return name, ""


# ---------------------------------------------------------------------------
# Database snapshot sync
# ---------------------------------------------------------------------------
async def sync_database_snapshot(db: AsyncSession, *, reason: str = "manual") -> dict:
    """Push a full DB JSON snapshot to ``backups/database/`` on Drive.

    Writes two files: a unique timestamped history file AND an in-place
    ``latest`` mirror. ``reason`` (e.g. "manual", "scheduled") is recorded in the
    history file name so you can see what triggered each snapshot.
    """
    if not is_enabled():
        return {"ok": False, "skipped": True, "reason": "drive_sync_disabled"}

    try:
        payload = await build_backup_payload(db)
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    except Exception as exc:
        logger.error("Drive snapshot: building payload failed: %s", exc)
        return {"ok": False, "error": f"payload_build_failed: {exc}"}

    path_parts = ["backups", "database"]
    history_name = build_name("db-snapshot", "system", reason, "json")
    latest_name = f"{_APP}{_FIELD_SEP}db-snapshot{_FIELD_SEP}system{_FIELD_SEP}latest.json"

    try:
        history = await asyncio.to_thread(
            google_drive.upload_file,
            path_parts=path_parts,
            filename=history_name,
            data=content,
            mimetype="application/json",
            update_existing=False,
        )
        latest = await asyncio.to_thread(
            google_drive.upload_file,
            path_parts=path_parts,
            filename=latest_name,
            data=content,
            mimetype="application/json",
            update_existing=True,  # keep a single, always-current mirror
        )
    except google_drive.DriveError as exc:
        logger.error("Drive snapshot upload failed: %s", exc)
        return {"ok": False, "error": str(exc)}

    logger.info(
        "Drive snapshot synced (reason=%s): %s (%d bytes)",
        reason, history.get("name"), len(content),
    )
    return {
        "ok": True,
        "reason": reason,
        "bytes": len(content),
        "counts": payload.get("counts", {}),
        "history": history,
        "latest": latest,
    }


# ---------------------------------------------------------------------------
# Attachment sync
# ---------------------------------------------------------------------------
async def sync_attachment(
    *,
    account_no: str,
    facility_id: str,
    original_name: str,
    data: bytes,
    mimetype: str = "application/octet-stream",
) -> dict:
    """Mirror a single uploaded document to Drive, filed by customer + facility.

    The name encodes ownership (which customer/facility) and the original
    document name, so a file is identifiable straight from its name in Drive.
    Best-effort: never raises, so a Drive hiccup can't fail the user's upload.
    """
    if not is_enabled():
        return {"ok": False, "skipped": True, "reason": "drive_sync_disabled"}

    acc = _field(account_no, "unknown")
    fac = _field(facility_id, "general") if (facility_id or "").strip() else "general"
    stem, ext = _split_ext(original_name)
    path_parts = ["attachments", f"cust-{acc}", f"fac-{fac}"]
    # descriptor binds the facility + original document stem into the name.
    descriptor = f"fac-{fac}--{_field(stem, 'document')}"
    filename = build_name("attachment", f"cust-{acc}", descriptor, ext)

    try:
        result = await asyncio.to_thread(
            google_drive.upload_file,
            path_parts=path_parts,
            filename=filename,
            data=data,
            mimetype=mimetype or "application/octet-stream",
            update_existing=False,
        )
    except google_drive.DriveError as exc:
        logger.error("Drive attachment sync failed (%s): %s", original_name, exc)
        return {"ok": False, "error": str(exc)}

    logger.info("Drive attachment synced: %s -> %s", original_name, result.get("name"))
    return {"ok": True, "result": result}


# ---------------------------------------------------------------------------
# Status + background scheduler
# ---------------------------------------------------------------------------
async def status() -> dict:
    """Report current sync configuration and verify the credentials authenticate."""
    base = {
        "enabled": settings.GOOGLE_DRIVE_ENABLED,
        "configured": is_enabled(),
        "root_folder_id": settings.GOOGLE_DRIVE_FOLDER_ID or None,
        "interval_hours": settings.DRIVE_SYNC_INTERVAL_HOURS,
    }
    if not is_enabled():
        base["connected"] = False
        return base
    try:
        info = await asyncio.to_thread(google_drive.about)
        base["connected"] = True
        base["service_account"] = (info.get("user") or {}).get("emailAddress")
    except google_drive.DriveError as exc:
        base["connected"] = False
        base["error"] = str(exc)
    return base


async def run_periodic_snapshot_sync() -> None:
    """Background loop: push a DB snapshot every DRIVE_SYNC_INTERVAL_HOURS.

    Started from the app lifespan only when sync is enabled. It opens its own DB
    session per run and swallows all errors so a transient failure never kills the
    loop. Cancellation (app shutdown) is propagated cleanly.
    """
    interval = max(1, settings.DRIVE_SYNC_INTERVAL_HOURS) * 3600
    logger.info("Drive periodic snapshot sync started (every %sh)", settings.DRIVE_SYNC_INTERVAL_HOURS)
    from app.database import AsyncSessionLocal

    while True:
        try:
            async with AsyncSessionLocal() as session:
                await sync_database_snapshot(session, reason="scheduled")
        except asyncio.CancelledError:
            logger.info("Drive periodic snapshot sync stopped")
            raise
        except Exception as exc:  # pragma: no cover - defensive, keep the loop alive
            logger.error("Drive periodic snapshot sync iteration failed: %s", exc)
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Drive periodic snapshot sync stopped")
            raise
