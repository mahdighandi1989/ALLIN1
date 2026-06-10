"""Low-level Google Drive client (Service Account, server-to-server).

This is the thin, synchronous wrapper around the Google Drive v3 API. It knows
nothing about the app's domain — it only knows how to authenticate with a Service
Account, ensure a nested folder path exists under the configured root, and
create/update a file inside it. The domain-aware orchestration (what to push,
how to name it, which sub-folder it belongs in) lives in ``drive_sync``.

Design notes / "why":
  * Service Account (not the OAuth refresh token) so backups run automatically
    without any user being logged in, and never expire mid-job.
  * The ``googleapiclient`` stack is synchronous and blocking, so every public
    function here is synchronous; async callers must hand them to a worker thread
    (``drive_sync`` does this via ``asyncio.to_thread``) to avoid blocking the
    event loop.
  * Heavy imports (``googleapiclient``/``google.auth``) are deferred to call time
    so the app still boots — and the test suite still imports — when the optional
    Drive dependencies aren't installed.
  * ``supportsAllDrives``/``includeItemsFromAllDrives`` are set everywhere so the
    same code works whether the destination folder lives in My Drive or a Shared
    Drive.
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
import threading
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Full drive scope: the sync root folder is created by a human and *shared* with
# the Service Account, so the narrower ``drive.file`` scope (app-created files
# only) cannot see it. Full scope lets us create sub-folders and files inside it.
_SCOPES = ["https://www.googleapis.com/auth/drive"]
_FOLDER_MIME = "application/vnd.google-apps.folder"

# Cached singletons. The Drive service is expensive to build; folder ids are
# cached so a repeated upload to the same category doesn't re-query/re-create the
# folder tree every time. Guarded by a lock because uploads may run concurrently
# (background sync + a request-triggered attachment upload).
_service = None
_folder_cache: dict[tuple[str, str], str] = {}
_lock = threading.Lock()


class DriveError(Exception):
    """Raised when a Drive operation fails or Drive is not configured."""


def is_configured() -> bool:
    """True when Drive sync is enabled and has its creds + root folder."""
    return settings.google_drive_configured()


def reset_cache() -> None:
    """Drop the cached service + folder ids (used by tests and after re-config)."""
    global _service
    with _lock:
        _service = None
        _folder_cache.clear()


def _load_credentials():
    """Build Service Account credentials from ``GOOGLE_CREDENTIALS_JSON``.

    Accepts either raw JSON or base64-encoded JSON, so the value survives being
    pasted into a dashboard env field that mangles newlines.
    """
    from google.oauth2 import service_account  # deferred (optional dependency)

    raw = settings.GOOGLE_CREDENTIALS_JSON.strip()
    if not raw:
        raise DriveError("GOOGLE_CREDENTIALS_JSON is empty")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        # Fall back to base64 -> JSON (dashboards often base64 multi-line secrets).
        try:
            info = json.loads(base64.b64decode(raw).decode("utf-8"))
        except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError) as exc:
            raise DriveError(
                "GOOGLE_CREDENTIALS_JSON is not valid JSON or base64-encoded JSON"
            ) from exc
    return service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)


def _get_service():
    """Return a cached, authenticated Drive v3 service handle."""
    global _service
    if _service is not None:
        return _service
    with _lock:
        if _service is not None:
            return _service
        try:
            from googleapiclient.discovery import build  # deferred import
        except ImportError as exc:  # dependency not installed
            raise DriveError(
                "google-api-python-client is not installed; add it to requirements"
            ) from exc
        creds = _load_credentials()
        # cache_discovery=False avoids a noisy warning + a file-cache write that
        # isn't wanted on an ephemeral container.
        _service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return _service


def _drive_error(action: str, exc: Exception) -> DriveError:
    """Wrap a Google ``HttpError`` (or any error) in a clean ``DriveError``."""
    return DriveError(f"Drive {action} failed: {type(exc).__name__}: {str(exc)[:300]}")


def _ensure_one_folder(service, name: str, parent_id: str) -> str:
    """Return the id of sub-folder ``name`` under ``parent_id``, creating it once.

    Idempotent: an existing folder with that name is reused, so repeated syncs do
    not pile up duplicate folders.
    """
    key = (parent_id, name)
    cached = _folder_cache.get(key)
    if cached:
        return cached
    with _lock:
        cached = _folder_cache.get(key)
        if cached:
            return cached
        safe = name.replace("'", "\\'")
        query = (
            f"name = '{safe}' and mimeType = '{_FOLDER_MIME}' "
            f"and '{parent_id}' in parents and trashed = false"
        )
        try:
            resp = (
                service.files()
                .list(
                    q=query,
                    fields="files(id, name)",
                    pageSize=1,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            files = resp.get("files", [])
            if files:
                folder_id = files[0]["id"]
            else:
                created = (
                    service.files()
                    .create(
                        body={
                            "name": name,
                            "mimeType": _FOLDER_MIME,
                            "parents": [parent_id],
                        },
                        fields="id",
                        supportsAllDrives=True,
                    )
                    .execute()
                )
                folder_id = created["id"]
        except Exception as exc:  # googleapiclient HttpError or transport error
            raise _drive_error(f"ensure folder '{name}'", exc) from exc
        _folder_cache[key] = folder_id
        return folder_id


def ensure_folder_path(path_parts: list[str]) -> str:
    """Ensure a nested folder path exists under the root and return the leaf id.

    ``path_parts`` is the category/type taxonomy, e.g. ``["attachments",
    "cust-1001", "fac-F1"]``. An empty list returns the root folder itself.
    """
    if not is_configured():
        raise DriveError("Google Drive sync is not configured")
    service = _get_service()
    parent = settings.GOOGLE_DRIVE_FOLDER_ID.strip()
    for part in path_parts:
        part = (part or "").strip()
        if not part:
            continue
        parent = _ensure_one_folder(service, part, parent)
    return parent


def _find_file(service, folder_id: str, name: str) -> Optional[str]:
    """Return the id of a file named ``name`` directly in ``folder_id`` (or None)."""
    safe = name.replace("'", "\\'")
    query = (
        f"name = '{safe}' and '{folder_id}' in parents and trashed = false "
        f"and mimeType != '{_FOLDER_MIME}'"
    )
    resp = (
        service.files()
        .list(
            q=query,
            fields="files(id, name)",
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files = resp.get("files", [])
    return files[0]["id"] if files else None


def upload_file(
    *,
    path_parts: list[str],
    filename: str,
    data: bytes,
    mimetype: str = "application/octet-stream",
    update_existing: bool = False,
) -> dict:
    """Create (or update) ``filename`` inside the folder at ``path_parts``.

    When ``update_existing`` is True and a file of the same name already exists in
    that folder, its content is replaced in place (used for the stable "latest"
    mirror so it stays a single, always-current file). Otherwise a new file is
    created — callers give those unique, timestamped names so each is a distinct,
    traceable historical artifact.

    Returns a small result dict ``{id, name, link, folder_id, action}``.
    """
    if not is_configured():
        raise DriveError("Google Drive sync is not configured")
    from googleapiclient.http import MediaInMemoryUpload  # deferred import

    service = _get_service()
    folder_id = ensure_folder_path(path_parts)
    media = MediaInMemoryUpload(data, mimetype=mimetype, resumable=False)
    try:
        existing_id = _find_file(service, folder_id, filename) if update_existing else None
        if existing_id:
            result = (
                service.files()
                .update(
                    fileId=existing_id,
                    media_body=media,
                    fields="id, name, webViewLink",
                    supportsAllDrives=True,
                )
                .execute()
            )
            action = "updated"
        else:
            result = (
                service.files()
                .create(
                    body={"name": filename, "parents": [folder_id]},
                    media_body=media,
                    fields="id, name, webViewLink",
                    supportsAllDrives=True,
                )
                .execute()
            )
            action = "created"
    except Exception as exc:
        raise _drive_error(f"upload '{filename}'", exc) from exc
    return {
        "id": result.get("id"),
        "name": result.get("name"),
        "link": result.get("webViewLink"),
        "folder_id": folder_id,
        "action": action,
    }


def about() -> dict:
    """Return a tiny liveness/identity probe for the configured Service Account.

    Used by the status endpoint to confirm the credentials actually authenticate
    and report the acting account, without uploading anything.
    """
    service = _get_service()
    try:
        info = (
            service.about()
            .get(fields="user(emailAddress, displayName), storageQuota(usage, limit)")
            .execute()
        )
    except Exception as exc:
        raise _drive_error("about", exc) from exc
    return info
