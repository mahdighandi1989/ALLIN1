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

# Scopes per auth mode:
#   • OAuth uses drive.file (least privilege — the app can only touch files it
#     creates, which is exactly the backup tree it owns).
#   • Service Account uses full drive, because its target root folder was created
#     by a human and merely *shared* with it (drive.file couldn't see that).
_OAUTH_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
_SA_SCOPES = ["https://www.googleapis.com/auth/drive"]
_FOLDER_MIME = "application/vnd.google-apps.folder"
_TOKEN_URI = "https://oauth2.googleapis.com/token"

# Cached singletons. The Drive service is expensive to build; folder ids are
# cached so a repeated upload to the same category doesn't re-query/re-create the
# folder tree every time. Guarded by a lock because uploads may run concurrently
# (background sync + a request-triggered attachment upload).
_service = None
_service_key = None  # what the cached service was built for (mode + token marker)
_oauth_token: str | None = None  # set by configure_oauth_token() before each op
_folder_cache: dict[tuple[str, str], str] = {}
_lock = threading.Lock()


class DriveError(Exception):
    """Raised when a Drive operation fails or Drive is not configured."""


def is_configured() -> bool:
    """True when Drive sync is enabled and has the config its mode needs."""
    return settings.google_drive_configured()


def configure_oauth_token(refresh_token: str | None) -> None:
    """Set the OAuth refresh token to authenticate as (OAuth mode only).

    Called by the async layer (which can read it from the DB) right before a
    Drive operation. Changing the token invalidates the cached service so the
    next call re-authenticates as the new account.
    """
    global _oauth_token, _service, _service_key
    if refresh_token != _oauth_token:
        with _lock:
            _oauth_token = refresh_token
            _service = None
            _service_key = None
            _folder_cache.clear()


def reset_cache() -> None:
    """Drop the cached service + folder ids (used by tests and after re-config)."""
    global _service, _service_key
    with _lock:
        _service = None
        _service_key = None
        _folder_cache.clear()


def _service_account_credentials():
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
    return service_account.Credentials.from_service_account_info(info, scopes=_SA_SCOPES)


def _oauth_credentials():
    """Build user OAuth credentials from the configured refresh token.

    google-auth refreshes the short-lived access token automatically using the
    refresh token + the app's client id/secret.
    """
    from google.oauth2.credentials import Credentials  # deferred import

    if not _oauth_token:
        raise DriveError(
            "Google Drive is not connected — no OAuth refresh token. Use the "
            "'Connect Google Drive' button in Settings."
        )
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
        raise DriveError("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are not set")
    return Credentials(
        token=None,
        refresh_token=_oauth_token,
        token_uri=_TOKEN_URI,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=_OAUTH_SCOPES,
    )


def _get_service():
    """Return a cached, authenticated Drive v3 service handle for the active mode."""
    global _service, _service_key
    mode = settings.drive_auth_mode()
    key = "sa" if mode == "service_account" else f"oauth:{_oauth_token}"
    if _service is not None and _service_key == key:
        return _service
    with _lock:
        if _service is not None and _service_key == key:
            return _service
        try:
            from googleapiclient.discovery import build  # deferred import
        except ImportError as exc:  # dependency not installed
            raise DriveError(
                "google-api-python-client is not installed; add it to requirements"
            ) from exc
        creds = _service_account_credentials() if mode == "service_account" else _oauth_credentials()
        # cache_discovery=False avoids a noisy warning + a file-cache write that
        # isn't wanted on an ephemeral container.
        _service = build("drive", "v3", credentials=creds, cache_discovery=False)
        _service_key = key
        return _service


def _root_parent(service) -> str:
    """Resolve the folder id that the sync tree is rooted at, per auth mode.

    Service Account: the human-created, shared folder id from config.
    OAuth: an app-created folder (named DRIVE_BACKUP_FOLDER) at the root of the
    connected user's My Drive — created once and reused (drive.file can manage the
    files it creates, so it cannot use an arbitrary pre-existing folder).
    """
    if settings.drive_auth_mode() == "service_account":
        folder = settings.GOOGLE_DRIVE_FOLDER_ID.strip()
        if not folder:
            raise DriveError("GOOGLE_DRIVE_FOLDER_ID is not set")
        return folder
    root_name = (settings.DRIVE_BACKUP_FOLDER or "ALLIN1-Drive").strip() or "ALLIN1-Drive"
    return _ensure_one_folder(service, root_name, "root")


# Human-friendly hints for the Google error reasons we're most likely to hit, so
# a truncated alert (e.g. in Telegram) still tells the operator what to actually fix.
_REASON_HINTS = {
    "storageQuotaExceeded": (
        "the Service Account has no Drive storage of its own. Either use a Shared "
        "Drive as the target folder, or switch Drive sync to OAuth (a real user's "
        "account provides the quota)."
    ),
    "accessNotConfigured": "enable the Google Drive API for this Cloud project.",
    "insufficientPermissions": "share the target folder with the Service Account's client_email as Editor.",
    "insufficientFilePermissions": "share the target folder with the Service Account's client_email as Editor.",
    "notFound": "the folder id is wrong or not shared with the Service Account.",
    "rateLimitExceeded": "Drive API rate limit hit; retry shortly.",
}


def _describe_http_error(exc: Exception) -> str | None:
    """Extract 'status reason — message [hint]' from a googleapiclient HttpError.

    Returns None when ``exc`` isn't a recognisable HttpError, so the caller falls
    back to the generic representation. The reason is placed FIRST so the cause
    survives any downstream truncation of the message.
    """
    content = getattr(exc, "content", None)
    status = getattr(getattr(exc, "resp", None), "status", None)
    if content is None:
        return None
    try:
        if isinstance(content, (bytes, bytearray)):
            content = content.decode("utf-8", "replace")
        err = json.loads(content).get("error", {})
    except (json.JSONDecodeError, AttributeError):
        return None
    code = err.get("code", status)
    message = err.get("message", "")
    errors = err.get("errors") or []
    reason = errors[0].get("reason") if errors and isinstance(errors[0], dict) else err.get("status")
    parts = [str(code) if code is not None else "", reason or ""]
    head = " ".join(p for p in parts if p).strip()
    hint = _REASON_HINTS.get(reason or "")
    out = f"{head} — {message}" if message else head
    if hint:
        out = f"{out} → Fix: {hint}"
    return out or None


def _drive_error(action: str, exc: Exception) -> DriveError:
    """Wrap a Google ``HttpError`` (or any error) in a clean ``DriveError``.

    For HTTP errors the Google reason/message/fix-hint go first so even a
    truncated alert is actionable; the long request URL is dropped.
    """
    described = _describe_http_error(exc)
    if described:
        return DriveError(f"Drive {action} failed: {described}")
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
    parent = _root_parent(service)
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
    data: bytes | None = None,
    file_path: str | None = None,
    mimetype: str = "application/octet-stream",
    update_existing: bool = False,
) -> dict:
    """Create (or update) ``filename`` inside the folder at ``path_parts``.

    Pass either ``data`` (in-memory bytes) or ``file_path`` (stream the content
    from disk — used for large DB snapshots so the whole file is never held in
    RAM at once).

    When ``update_existing`` is True and a file of the same name already exists in
    that folder, its content is replaced in place (used for the stable "latest"
    mirror so it stays a single, always-current file). Otherwise a new file is
    created — callers give those unique, timestamped names so each is a distinct,
    traceable historical artifact.

    Returns a small result dict ``{id, name, link, folder_id, action}``.
    """
    if not is_configured():
        raise DriveError("Google Drive sync is not configured")

    service = _get_service()
    folder_id = ensure_folder_path(path_parts)
    if file_path is not None:
        from googleapiclient.http import MediaFileUpload  # deferred import
        media = MediaFileUpload(file_path, mimetype=mimetype, resumable=True)
    else:
        from googleapiclient.http import MediaInMemoryUpload  # deferred import
        media = MediaInMemoryUpload(data or b"", mimetype=mimetype, resumable=False)
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


def download_file(file_id: str) -> bytes:
    """Fetch the full byte content of a Drive file by id.

    Used to stream an attachment back to the client when Drive is the primary
    store. Raises ``DriveError`` on any failure so the caller can fall back or
    surface a clean error.
    """
    if not file_id:
        raise DriveError("download_file called with empty file id")
    import io
    from googleapiclient.http import MediaIoBaseDownload  # deferred import

    service = _get_service()
    try:
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buffer.getvalue()
    except Exception as exc:
        raise _drive_error(f"download '{file_id}'", exc) from exc


def delete_file(file_id: str) -> None:
    """Permanently delete a Drive file by id (best-effort, raises on hard failure).

    A missing file (already gone) is treated as success so deletes are idempotent.
    """
    if not file_id:
        return
    service = _get_service()
    try:
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
    except Exception as exc:
        # 404 == already deleted; don't treat that as an error.
        if "404" in str(exc) or "notFound" in str(exc):
            return
        raise _drive_error(f"delete '{file_id}'", exc) from exc


def service_account_email() -> str | None:
    """Best-effort: the client_email from the Service Account JSON (for display)."""
    raw = settings.GOOGLE_CREDENTIALS_JSON.strip()
    if not raw:
        return None
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        try:
            info = json.loads(base64.b64decode(raw).decode("utf-8"))
        except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError):
            return None
    return info.get("client_email")


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
